import json
import unicodedata
from pathlib import Path
from fastapi import HTTPException
from app.database.mongodb import get_database

CATALOGO = json.loads((Path(__file__).resolve().parents[1] / 'knowledge/catalogo_alimentos.json').read_text(encoding='utf-8'))


def normalizar(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.strip().casefold()) if not unicodedata.combining(c))


async def validar_clasificacion(tenant, familia, categoria):
    family_key, category_key = normalizar(familia), normalizar(categoria)
    aliases = {'cereales y granos': 'granos y pastas', 'verduras': 'verduras y hortalizas'}
    family_key = aliases.get(family_key, family_key)
    for group in CATALOGO:
        for family, categories in group['familias'].items():
            if normalizar(family) == family_key:
                match = next((c for c in categories if normalizar(c) == category_key), None)
                if match:
                    return family, match
                existing = await get_database()["productos"].find_one({'id_empresa': tenant, 'familia': familia, 'categoria': categoria})
                if existing:
                    return familia, categoria
                raise HTTPException(422, 'La categoría no pertenece a la familia seleccionada')
    # Preserve classifications actually present before deployment; they are not
    # inferred from supplier input and are never silently reclassified.
    existing = await get_database()["productos"].find_one({'id_empresa': tenant,
        'familia': familia, 'categoria': categoria})
    if existing:
        return familia, categoria
    raise HTTPException(422, 'Familia o categoría no registrada en el catálogo')
