"""Exact calendar contract supplied by the author of the Kaggle experiment."""
from datetime import date

COVARIATES = ['month', 'day', 'dayofweek', 'is_weekend', 'dayofyear', 'weekofyear', 'quarter', 'is_campana_navidena']


def calendar_values(day: date) -> dict[str, int]:
    return {'month': day.month, 'day': day.day, 'dayofweek': day.weekday(),
            'is_weekend': int(day.weekday() >= 5), 'dayofyear': day.timetuple().tm_yday,
            'weekofyear': day.isocalendar().week, 'quarter': (day.month - 1) // 3 + 1,
            'is_campana_navidena': int(day.month == 12)}


def series_id(id_almacen: str, id_producto: str) -> str:
    return str(id_almacen) + '_' + str(id_producto)
