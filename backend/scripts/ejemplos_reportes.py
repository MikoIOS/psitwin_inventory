"""Generate clearly labelled examples in an isolated MongoDB, never application data."""
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from tests.test_google_auth import isolated_database
from tests.test_plano_reportes import sample
from app.dto.inventario_consulta_dto import InventarioFiltros
from app.services.inventario_reportes_service import preparar_datos
from app.services.inventario_reportes_archivos import generar_archivo

async def main():
    root = Path(__file__).resolve().parents[2]
    output = root / 'outputs' / 'psitwin_reportes_20261029'
    output.mkdir(parents=True, exist_ok=True)
    with pytest.MonkeyPatch.context() as patch:
        async with isolated_database(patch) as db:
            _, _, company, levels = await sample(db)
            # Example data exists only inside a disposable database with a test prefix.
            for n in range(16):
                await db.productos.insert_one({'id_producto':f'example-{n}','id_empresa':'e','nombre':f'Producto controlado {n+1:02d} - lote de demostración','unidad':'kg' if n%2 else 'unidad','familia':'Alimentos','categoria':'Ejemplo'})
                await db.detalles_inventario.insert_one({'id_detalle_inventario':f'example-{n}','id_inventario':'i','id_producto':f'example-{n}','id_rack':'r','id_nivel':levels[n%4]['id_nivel'],'stock_actual':n+1,'stock_minimo':2,'stock_maximo':12})
            data = await preparar_datos(company, InventarioFiltros())
            data['alcance'] += ' · DATOS DE PRUEBA, NO PRODUCCIÓN'
            for fmt in ('pdf','xlsx'):
                content, _, name = generar_archivo(data, fmt)
                path = output / name
                path.write_bytes(content)
                print(f'{path}: {len(content)} bytes')
    import fitz
    renders = root / 'artifacts' / 'reportes-render.local'
    renders.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(output / 'inventario.pdf')
    for i, page in enumerate(doc):
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(renders / f'pdf-{i+1}.png')
    print(f'PDF pages rendered: {len(doc)}')
    # Inspect the saved workbook's actual cell values and styles in readable previews.
    # This is a rendering of cells, not a claim of a native Excel application test.
    from openpyxl import load_workbook
    from PIL import Image, ImageDraw, ImageFont
    import textwrap
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    bold = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
    wb = load_workbook(output / 'inventario.xlsx')
    for sheet in wb:
        for first in range(0, sheet.max_column, 7):
            columns = min(7, sheet.max_column-first)
            image = Image.new('RGB',(columns*210, (sheet.max_row+1)*72),'white')
            draw = ImageDraw.Draw(image)
            for ri, row in enumerate(sheet.iter_rows(min_col=first+1,max_col=first+columns)):
                for ci, cell in enumerate(row):
                    x,y=ci*210,ri*72
                    header = ri in (0,5)
                    draw.rectangle((x,y,x+210,y+72),fill='#14263D' if header else '#EEF3F8' if ri%2 else '#FFFFFF',outline='#CBD5E1')
                    value = str(cell.value) if cell.value is not None else ''
                    draw.multiline_text((x+6,y+5),'\n'.join(textwrap.wrap(value,24)),font=bold if header else font,fill='white' if header else '#14263D',spacing=3)
            image.save(renders / f'xlsx-{sheet.title}-{first//7+1}.png')
    print('Workbook: four sheets rendered, wide sheets split into consecutive column panels.')

if __name__ == '__main__': asyncio.run(main())
