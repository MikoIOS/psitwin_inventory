# IA remota en EC2: Saiki y AutoGluon existentes

Estado: implementación preparada para pruebas; no configura AWS, DNS, TLS ni Render.
Vercel llama al backend habitual. Render conserva autenticación, permisos de empresa,
MongoDB, el prompt, historial, selección y ejecución de herramientas de Saiki.
EC2 ejecuta únicamente inferencias: Qwen3:4b mediante Ollama y el WeightedEnsemble
AutoGluon 1.6.1 existente, sin entrenamiento ni pronósticos sustitutos.

## Contrato de red

- `GET /health`: proceso de API activo; **no afirma** que ambos modelos estén listos.
- `GET /api/tags`, `POST /api/chat`: protocolo de Ollama, incluyendo streaming NDJSON
  y tool calls. Solo permite el modelo configurado. No expone pull/delete/execute.
- `GET /forecast/status`: estado real y fingerprint del artefacto validado existente.
- `POST /forecast`: `{tenant, identifier, history: [{fecha, cantidad}]}`; al menos
  91 días consecutivos. Devuelve `{result, cached}` del runtime original.
- Todos requieren `Authorization: Bearer <AI_SERVICE_API_KEY>`.
- El servicio no tiene acceso a MongoDB ni necesita las credenciales de usuarios.
  `tenant` debe proceder del usuario autorizado en Render, nunca directamente del navegador.
- Límite de cuerpo 2 MB; un trabajo de inferencia a la vez; devuelve 429 si está ocupado.
  No se prometen concurrencia ni tiempos de respuesta hasta medirlos en EC2.

## Archivos preparados

`backend/ai_service/main.py`, `requirements.txt`, `ec2.env.example` y
`psitwin-ai.service.example`. El servicio se importa separado de `app.main`,
sin arrancar MongoDB, MQTT ni el servidor principal.

## Preparación de EC2 (requiere aprobación antes de aplicar)

1. Copiar el código revisado a `/opt/psitwin/backend` y crear un entorno virtual
   `/opt/psitwin/api`. Instalar ahí `backend/ai_service/requirements.txt`.
2. Crear `/etc/psitwin-ai.env` usando el ejemplo. Generar una clave aleatoria de
   al menos 32 caracteres y proteger el archivo; no subirla a Git ni al frontend.
3. Ejecutar una única instancia de Uvicorn en `127.0.0.1:8100`; Ollama permanece
   en `127.0.0.1:11434`. No abrir 8100 ni 11434 al público.
4. Configurar proxy HTTPS con certificado válido y un nombre DNS estable apuntando
   a la Elastic IP. Desactivar buffering del proxy para `/api/chat`, permitir cuerpos
   de 2 MB y ajustar el timeout de lectura a más de 300 segundos. Abrir solo el acceso
   necesario a HTTPS; decidir reglas de red y dominio antes de desplegar.
5. Probar autenticación, rechazo sin clave, streaming y herramientas desde Render.
   `GET /api/tags` confirma el modelo descargado; una consulta real confirma inferencia.

## Modelo AutoGluon

No copiar una venv de Windows: crear entorno Linux separado y configurar
`AUTOGLUON_PYTHON` con su ejecutable absoluto. Instalar las versiones de
`backend/requirements-autogluon.txt` **después de revisar espacio y compatibilidad**.
Copiar artefactos de confianza completos y pesos Hugging Face requeridos por Chronos2
/Toto2, conservando las rutas esperadas por el worker. El worker usa
`artifacts/huggingface.local` con `HF_HUB_OFFLINE=1`.
Copiar el directorio `psitwin_forecasting`, incluido `modelo_evaluacion`, y ejecutar
la validación real existente para generar `runtime_validation.json` con el fingerprint
correcto. Sin ella el servicio reporta MODELO_NO_DISPONIBLE; `/health` puede seguir activo.

Con 8.3 GB libres después de Ollama, medir tamaño de artefactos/dependencias antes
de instalar: no asumir que todo cabe. Qwen se descarga de memoria al terminar cada
consulta (`keep_alive=0`); el worker AutoGluon se cierra tras cada petición para dejar
memoria disponible, conservando caché en disco. Esto implica más latencia de carga.
La viabilidad de ambos modelos en 8 GiB requiere una prueba real, especialmente el ensemble.

## Variables de Render (no aplicar hasta HTTPS verificado)

```dotenv
OLLAMA_BASE_URL=https://ia.TU-DOMINIO
AUTOGLUON_REMOTE_URL=https://ia.TU-DOMINIO
AI_SERVICE_API_KEY=misma-clave-privada-de-EC2
OLLAMA_MODEL=qwen3:4b
AUTOGLUON_TIMEOUT_SECONDS=300
```

No añadir prefijo `/api/v1`: estos endpoints pertenecen al servicio de inferencia.
No poner la clave en `VITE_*`. Mantener la verificación TLS habilitada. Sin
`AUTOGLUON_REMOTE_URL`, Render conserva el runtime local anterior; sin clave Saiki
conserva sus llamadas locales anteriores. Los clientes remotos fallan explícitamente
si EC2 está apagada, sin inventar resultados.

## Pruebas y operación

Las pruebas de transporte usan mocks de inferencia: no sustituyen la validación de
los modelos reales en EC2. Antes de presentar: arrancar EC2, esperar checks, verificar
HTTPS, modelos y una consulta real de Saiki y de pronósticos con empresa autorizada.
La Elastic IP conserva su dirección mientras esté reservada; sigue teniendo costo
con la instancia apagada. Autorizar cada cambio operativo por separado.

## Operación sin dominio comprado

Let’s Encrypt admite certificados de IP de corta duración. El instalador
`backend/ai_service/install_ec2.sh` prepara Nginx con ACME HTTP en 80 y el proxy
HTTPS en 443 para la Elastic IP de esta instancia. Instala Certbot >=5.4,<6 en
un entorno separado, solicita un certificado de producción y crea un timer de
renovación. Estos certificados duran alrededor de seis días: al reencender una
instancia que estuvo apagada varios días, comprobar/renovar antes de la presentación.
El timer intenta renovar cinco minutos después del arranque y cada doce horas.
La emisión acepta los términos de Let's Encrypt y publica la IP en los registros
públicos de certificados; no envía la clave privada del servicio ni datos de inventario.

El script se detiene si encuentra servidores usando 80/443 o configuración anterior
con el mismo nombre. Si una etapa falla, conservar el error y revisar antes de
repetirlo; no es un instalador de recuperación automática. No configura firewalls
UFW ni ACL de VPC; comprobarlos si ACME o HTTPS no llegan al servidor.

`configure_aws_network.py` se ejecuta desde la PC con AWS CLI y crea un grupo de
seguridad exclusivo para esta EC2, preservando los grupos anteriores. Permite 80
para validación ACME y 443 para la API autenticada. No modifica los grupos de las
otras instancias ni abre Ollama o Uvicorn. No valida que los grupos preexistentes
carezcan de reglas amplias; esa revisión sigue siendo necesaria si existen.

El servicio systemd generado usa `/home/ubuntu/psitwin-ai`, reemplaza el proceso
manual de esa carpeta y arranca Ollama y la API automáticamente al encender EC2.
`verify_ec2.py --base-url https://35.171.142.151` comprueba TLS, rechazo sin clave,
inferencia, llamada a herramientas y streaming, con solicitudes de prueba sin MongoDB.

Durante las pruebas reales en EC2, `qwen3:4b` agotó el presupuesto generando
razonamiento. Se probó y autorizó `qwen3:4b-instruct`: respuestas y tool calls
funcionaron. Render debe usar `OLLAMA_MODEL=qwen3:4b-instruct`. No se añade el
interruptor híbrido `/no_think` a esta variante instruct.

Fuentes: https://letsencrypt.org/2026/03/11/shorter-certs-certbot

## Despliegue desde el repositorio de Dylan

Usar el repositorio `https://github.com/DylanCabezas/PsiTwin_inventory.git`.
Los cambios de IA deben estar publicados en la rama que se clone, antes de ejecutar
comandos de instalación. La publicación en una rama no despliega ni cambia main.

En EC2, clonar la rama revisada en `~/psitwin-ai/repo`. Se conservan el entorno
`~/psitwin-ai/api` y la configuración privada `~/psitwin-ai/service.env` fuera del clon.
Ejecutar el instalador desde `~/psitwin-ai/repo/backend/ai_service/install_ec2.sh`;
el servicio systemd usa el backend del clon como WorkingDirectory y reemplaza
el proceso manual anterior. No copiar service.env a Git.

Los pesos entrenados de AutoGluon siguen siendo necesarios: clonar el código no
sustituye `modelo_evaluacion`, datos de validación y los pesos foundation requeridos.

## EC2 con Apache preinstalado

Si el puerto 80 pertenece al Apache predeterminado de Ubuntu y 443 está libre,
usar `bash ~/psitwin-ai/repo/backend/ai_service/install_ec2_apache.sh` en lugar
del instalador Nginx. Conserva `000-default.conf` y añade `psitwin-ai.conf`,
seleccionado por la IP pública como ServerName. El nuevo sitio HTTP solo sirve
el webroot de ACME; el proxy a la API existe únicamente en HTTPS.

Habilita ssl, proxy, proxy_http y headers; mantiene ProxyRequests Off, reenvía
a Uvicorn en localhost y ejecuta apache2ctl configtest antes de cada recarga.
Certbot usa webroot (no el plugin apache, que no soporta emisión para IP en
esta configuración); el timer recarga Apache tras renovar el certificado.
No elimina ni deshabilita Apache ni su sitio predeterminado.

Si falla una etapa, conservar el error y revisar antes de repetir. No se ha
probado la emisión real desde la sesión de desarrollo; requiere ejecutar en EC2
y validar el certificado, streaming y herramientas con verify_ec2.py.
