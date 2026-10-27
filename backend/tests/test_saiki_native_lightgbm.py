"""Real native models, synthetic features; no MongoDB or pandas pipeline."""
import ast
import ctypes
from datetime import date, datetime, timedelta
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
DLL = ROOT / ".venv/Lib/site-packages/lightgbm/bin/lib_lightgbm.dll"


@unittest.skipUnless(sys.platform == "win32" and DLL.exists(), "Existing Windows LightGBM DLL required")
class NativeLightGBMTests(unittest.TestCase):
    def test_real_seven_day_models_and_horizon_rejection(self):
        lib = ctypes.CDLL(str(DLL))
        lib.LGBM_GetLastError.restype = ctypes.c_char_p
        def checked(result):
            if result != 0:
                raise RuntimeError(lib.LGBM_GetLastError().decode())

        handles = {}
        try:
            for horizon in range(1, 8):
                handle = ctypes.c_void_p()
                iterations = ctypes.c_int()
                path = ROOT / f"app/ml/models/psitwin_v3_6/models/L1_FAST__global_D{horizon}.txt"
                checked(lib.LGBM_BoosterCreateFromModelfile(str(path).encode(), ctypes.byref(iterations), ctypes.byref(handle)))
                handles[horizon] = handle

            class NativeModel:
                def __init__(self, handle):
                    self.handle = handle
                def predict(self, features):
                    width = ctypes.c_int()
                    checked(lib.LGBM_BoosterGetNumFeature(self.handle, ctypes.byref(width)))
                    self_test.assertEqual(width.value, 136)
                    row = (ctypes.c_double * width.value)(*features)
                    output = (ctypes.c_double * 1)()
                    count = ctypes.c_int64()
                    checked(lib.LGBM_BoosterPredictForMat(self.handle, ctypes.cast(row, ctypes.c_void_p), ctypes.c_int(1), ctypes.c_int32(1), ctypes.c_int32(width.value), ctypes.c_int(1), ctypes.c_int(0), ctypes.c_int(0), ctypes.c_int(-1), b"num_threads=1", ctypes.byref(count), output))
                    self_test.assertEqual(count.value, 1)
                    return [output[0]]

            self_test = self
            tree = ast.parse((ROOT / "app/ml/predictor.py").read_text(encoding="utf-8-sig"))
            cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DemandPredictor")
            module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[])
            ast.fix_missing_locations(module)
            namespace = {"date": date, "datetime": datetime, "timedelta": timedelta}
            exec(compile(module, "predictor.py", "exec"), namespace)
            predictor = namespace["DemandPredictor"].__new__(namespace["DemandPredictor"])
            predictor.loader = SimpleNamespace(get_global_model=lambda horizon: NativeModel(handles[horizon]))
            predictor.feature_builder = SimpleNamespace(build_row=lambda features: features)
            features = {horizon: [float("nan")] * 136 for horizon in range(1, 8)}
            started = time.perf_counter()
            result = predictor.predict_7_days(features, date(2026, 1, 1))
            duration = (time.perf_counter() - started) * 1000
            self.assertEqual([item["horizonte"] for item in result["predicciones_diarias"]], list(range(1, 8)))
            self.assertEqual(result["predicciones_diarias"][-1]["fecha"], "2026-01-08")
            self.assertTrue(all(math.isfinite(item["demanda_predicha"]) and item["demanda_predicha"] >= 0 for item in result["predicciones_diarias"]))
            for horizon in (0, 8, 30):
                with self.assertRaises(ValueError):
                    predictor.predict_horizon(features[1], horizon)
            print(f"Native seven-day inference, synthetic missing features: {duration:.3f} ms; seven real models; zero Ollama calls")
        finally:
            for handle in handles.values():
                checked(lib.LGBM_BoosterFree(handle))


if __name__ == "__main__":
    unittest.main()
