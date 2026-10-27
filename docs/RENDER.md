# Publicación en GitHub y Render

## GitHub

El destino es `git@github.com:MikoIOS/psitwin_inventory.git`.
El paquete `psitwin-inventory.bundle`, si se adjunta a esta entrega, contiene una
rama `main` con un único commit inicial. Autor y committer:
`M41_K1 <miguel.espinoza.a@utec.edu.pe>` (identidad Git local).
Para que GitHub vincule la autoría a MikoIOS, ese correo debe estar asociado a tu cuenta.
El paquete no contiene `.env`, dependencias instaladas ni datos de MongoDB.

Desde una terminal con acceso a GitHub, en una carpeta nueva:

```bash
git clone /ruta/absoluta/psitwin-inventory.bundle psitwin-publicacion
cd psitwin-publicacion
git remote set-url origin git@github.com:MikoIOS/psitwin_inventory.git
git log --format='%an <%ae> | %cn <%ce>'
git push -u origin main
```

Esto requiere que el repositorio de destino esté vacío y que tu clave SSH tenga
permiso de escritura. Si ya contiene commits, el push puede ser rechazado: revisa
su contenido antes de sustituir el historial. No se requiere `--force` para un repo vacío.

## MongoDB Atlas

1. Crea un clúster y un usuario de base de datos con acceso a `psitwin_inventory`.
2. Autoriza en Network Access los rangos de salida indicados por tu servicio Render.
3. Copia la URI `mongodb+srv://...`, incluyendo usuario y contraseña correctamente
   codificados. Guárdala como secreto `MONGODB_URL` en Render, nunca en GitHub.

Usa una base nueva o una base migrada al esquema de inventario v2. La API crea
índices al iniciar y rechaza inventarios legacy pendientes de migración.
Los datos y las cuentas demo locales no se copian con el código.

## Render

1. En Render selecciona **New → Blueprint** y conecta `MikoIOS/psitwin_inventory`,
   rama `main`. Render detectará `render.yaml`.
2. Completa los valores solicitados:

   | Servicio | Variable | Valor |
   |---|---|---|
   | API | `MONGODB_URL` | URI privada de Atlas |
   | API | `CORS_ORIGINS` | URL pública HTTPS del frontend, sin barra final |
   | API | `FRONTEND_URL` | La misma URL del frontend |
   | Frontend | `VITE_API_URL` | URL pública HTTPS de la API seguida de `/api/v1` |

   Los nombres del Blueprint son `psitwin-backend` y `psitwin-frontend`, pero Render
   puede asignar URLs con sufijos. Confirma las URLs reales en el panel después de
   crear los servicios. Si todavía no las conoces, usa las previstas inicialmente
   y corrígelas después. Cambiar `VITE_API_URL` requiere reconstruir el frontend;
   cambiar CORS requiere volver a desplegar la API.
3. `SECRET_KEY` se genera automáticamente. MongoDB es externo; no se crea mediante
   este Blueprint. La API pide el plan `free`; confirma disponibilidad y cualquier
   coste mostrado por Render antes de crear recursos.
4. Verifica `https://<api>/health`: debe indicar `status: healthy` y `database: ok`.
   Actualmente el endpoint también responde HTTP 200 si MongoDB falla, por lo que
   debes comprobar el JSON y los logs, además del estado del despliegue.
5. Abre el frontend, registra una empresa y comprueba inicio de sesión e inventario.
   Recarga una ruta interna para verificar la regla SPA.

El Blueprint sigue los campos documentados en
[Render Blueprint YAML Reference](https://render.com/docs/blueprint-spec).

## Servicios adicionales

- MQTT y correo están desactivados inicialmente. Para sensores necesitas un broker
  externo y configurar `MQTT_ENABLED`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER` y
  `MQTT_PASSWORD`; comprueba sus requisitos de transporte antes de conectarlo.
- Ollama no se instala en este despliegue. `localhost:11434` no apunta a tu PC:
  configura `OLLAMA_BASE_URL` con un servicio accesible desde la API para habilitar
  las respuestas que dependen del modelo. No publiques un Ollama sin protección.
- El contenedor incluye los modelos LightGBM del repositorio. Comprueba consumo
  de memoria en Render al usar predicciones; el plan gratuito puede resultar
  insuficiente para algunas cargas.
- La revisión local no sustituye una prueba de conexión real con Atlas y Render.
