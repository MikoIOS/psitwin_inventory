import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'docs/plantillas_tienda');
const preview=path.join(root,'artifacts/piloto.local/plantillas');
await fs.mkdir(out,{recursive:true}); await fs.mkdir(preview,{recursive:true});
const tables=[
 ['Catalogo',['origen_datos','sku_tienda','nombre','marca','categoria','familia','presentacion','unidad_base','unidades_por_caja','peso_kg_unidad','precio_compra_pen','precio_venta_pen','proveedor_codigo','lead_time_dias','vida_util_dias','requiere_refrigeracion'],
 ['SIMULADO','PIL-001','Arroz 1 kg','Marca ejemplo','Granos','Abarrotes','Bolsa 1 kg','bolsa',12,1,3.2,4,'PROV-01',2,180,'NO']],
 ['Stock',['origen_datos','fecha_corte_lima','sku_tienda','almacen','zona','rack','stock_fisico','stock_sistema','reservado','no_vendible','stock_minimo','stock_maximo','lote','fecha_vencimiento','responsable_rol'],
 ['SIMULADO','2026-10-27 09:00','PIL-001','Principal','Secos','B-01',30,32,2,0,5,100,'LOTE-EJEMPLO','2027-01-15','Encargado']],
 ['Ventas',['origen_datos','fecha_lima','sku_tienda','local_codigo','unidades_vendidas','unidades_devueltas','estado_dia','promocion','fuente_documento'],
 ['SIMULADO','2026-10-26','PIL-001','LOCAL-01',8,0,'ABIERTO_CON_STOCK','NO','POS-EJEMPLO-01']],
 ['Proveedores',['origen_datos','proveedor_codigo','nombre_alias','dias_entrega_estimados','dias_entrega_min','dias_entrega_max','dias_visita','pedido_minimo_unidades','costo_envio_pen'],
 ['SIMULADO','PROV-01','Proveedor ejemplo',2,1,4,'Martes',12,10]],
 ['Reposicion',['origen_datos','pedido_codigo','sku_tienda','proveedor_codigo','fecha_necesidad','fecha_pedido','fecha_prometida','fecha_recepcion','cantidad_pedida_base','cantidad_recibida_base','frecuencia_compra_dias','estado'],
 ['SIMULADO','PED-001','PIL-001','PROV-01','2026-10-23','2026-10-24','2026-10-26','2026-10-26',24,24,7,'RECIBIDO']],
 ['Movimientos',['origen_datos','evento_codigo','fecha_hora_lima','sku_tienda','almacen_origen','rack_origen','almacen_destino','rack_destino','tipo','motivo','cantidad_base','documento','responsable_rol'],
 ['SIMULADO','MOV-001','2026-10-27 10:00','PIL-001','Principal','B-01','','','SALIDA','VENTA',8,'POS-EJEMPLO-01','Operario']],
];
const wb=Workbook.create();
for(const [name,headers,example] of tables){
 const sheet=wb.worksheets.add(name); sheet.showGridLines=false;
 const cols=headers.length;
 const region=sheet.getRangeByIndexes(0,0,22,cols);
 region.format.font.name='Arial'; region.format.font.size=10; region.format.columnWidth=23; region.format.rowHeight=24;
 sheet.getRangeByIndexes(0,0,1,cols).values=[headers];
 sheet.getRangeByIndexes(0,0,1,cols).format.fill='#172B4D';
 sheet.getRangeByIndexes(0,0,1,cols).format.font.color='#FFFFFF';
 sheet.getRangeByIndexes(0,0,1,cols).format.font.bold=true;
 sheet.getRangeByIndexes(0,0,1,cols).format.wrapText=true;
 sheet.getRangeByIndexes(0,0,1,cols).format.rowHeight=42;
 sheet.getRangeByIndexes(1,0,1,cols).values=[example];
 sheet.getRangeByIndexes(1,0,1,cols).format.fill='#FFF2CC';
 sheet.getRangeByIndexes(2,0,20,cols).format.fill='#F5F9FF';
 sheet.freezePanes.freezeRows(1); sheet.freezePanes.freezeColumns(2);
 sheet.getRange('A3:A22').dataValidation={rule:{type:'list',values:['REAL','SIMULADO']}};
 // Codes and ISO dates are deliberately text: preserve leading zeros and locale.
 const csv=[headers,example].map(row=>row.map(value=>'"'+String(value).replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
 await fs.writeFile(path.join(out,name.toLowerCase()+'.csv'),'\uFEFF'+csv,'utf8');
 const png=await wb.render({sheetName:name,range:`A1:${String.fromCharCode(64+cols)}5`,scale:1,format:'png'});
 await fs.writeFile(path.join(preview,name+'.png'),new Uint8Array(await png.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(path.join(out,'PLANTILLA_LEVANTAMIENTO_PSITWIN.xlsx'));
console.log((await wb.inspect({kind:'sheet',include:'id,name',maxChars:1800})).ndjson);
console.log('6 CSV y 1 XLSX creados; ejemplos exclusivamente SIMULADOS.');
