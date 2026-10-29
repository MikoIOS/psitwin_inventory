"""Extract the supplied archive into the private artifact directory. Never unpickles or fits."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--destino', type=Path, default=Path('artifacts/autogluon.local'))
    args = parser.parse_args()
    root = args.destino.resolve()
    with zipfile.ZipFile(args.zip) as archive:
        metadata = json.loads(archive.read('psitwin_forecasting/metadata.json'))
        if metadata['version_autogluon'] != '1.6.1' or metadata['horizonte_dias'] != 90 or metadata['modelo_final_entrenado'] is not False:
            raise SystemExit('Contrato del artefacto no compatible con esta integración')
        if sum(info.file_size for info in archive.infolist()) > 1_000_000_000:
            raise SystemExit('Archivo demasiado grande para el paquete esperado')
        for info in archive.infolist():
            target = (root / info.filename).resolve()
            if not target.is_relative_to(root) or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise SystemExit('Ruta insegura o enlace en el archivo')
            if info.is_dir(): continue
            data = archive.read(info)
            if target.exists() and target.read_bytes() != data:
                raise SystemExit('No se sobrescribe un artefacto diferente: ' + str(target))
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists(): target.write_bytes(data)
    print(json.dumps({'extracted': str(root / 'psitwin_forecasting'), 'zip_sha256': hashlib.sha256(args.zip.read_bytes()).hexdigest(),
                      'weights_in_zip': False, 'note': 'Ejecutar verificar_autogluon.py antes de habilitar inferencia.'}, indent=2))


if __name__ == '__main__': main()
