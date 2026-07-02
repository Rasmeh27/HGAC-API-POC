# Backend HGAC API

Backend FastAPI para una prueba de concepto de monitoreo y validación de cruces vehiculares en entorno portuario HGAC/HIT. El sistema integra lectura de placas y rótulos por cámara RTSP, eventos BioStar, consultas RNTT/Navis, ubicación GPS Wialon y consumo desde Ignition Perspective.

> Alcance: PoC operativo local. No debe tratarse como sistema productivo de control de acceso hasta completar persistencia, auditoría, hardening de seguridad, monitoreo de servicios y validaciones oficiales contra las fuentes maestras.

---

## 1. Descripción del repositorio para GitHub

Usar esta descripción en el campo **Description** del repositorio:

```text
Backend FastAPI para PoC de monitoreo y validación de cruces vehiculares portuarios HGAC. Integra LPR RTSP/SimpleLPR, BioStar, RNTT, Navis, Wialon e Ignition mediante APIs REST y puente JSON.
```

Longitud aproximada: 199 caracteres. Está por debajo del límite de GitHub de 350 caracteres.

---

## 2. Objetivo del proyecto

El backend centraliza las integraciones necesarias para evaluar y monitorear eventos de cruce vehicular en un gate portuario:

- Captura de frames desde webcam o cámara IP RTSP.
- Lectura LPR de placas y rótulos dominicanos.
- Publicación del último resultado LPR para Ignition.
- Lectura de eventos de acceso desde BioStar local/remoto.
- Consulta de chofer/camión en RNTT.
- Consulta de información operativa en Navis.
- Consulta de unidades GPS y geocercas en Wialon.
- Exposición REST para Ignition Perspective y para pruebas manuales desde Swagger.

El objetivo de la PoC es demostrar el flujo completo de observación y validación sin acoplar Ignition directamente a las cámaras ni a los sistemas externos.

---

## 3. Arquitectura funcional

```text
Ignition Perspective
        |
        | REST / JSON / URLs de evidencia
        v
Backend HGAC API - FastAPI
        |
        |-- CameraService
        |     |-- Webcam provider
        |     |-- RTSP provider
        |     |-- MJPEG stream manager
        |
        |-- LPR Module
        |     |-- OpenCV + EasyOCR bajo demanda
        |     |-- SimpleLPR continuo sobre RTSP
        |     |-- Catálogo operativo de patrones dominicanos
        |     |-- Evidencia: frames y crops
        |
        |-- BioStar Integration
        |     |-- BioStar remoto
        |     |-- Monitor local de lector
        |
        |-- RNTT Integration
        |     |-- ASMX / consulta chofer-camión
        |
        |-- Navis Integration
        |     |-- API interna HIT / OAuth
        |
        |-- Wialon Integration
              |-- GPS Gurtam
              |-- Estado online
              |-- Geocercas terminal/gate
```

---

## 4. Stack técnico

| Capa | Tecnología |
|---|---|
| API | FastAPI |
| Runtime | Python 3.11+ recomendado |
| Validación de datos | Pydantic / pydantic-settings |
| Cámara | OpenCV, webcam o RTSP |
| LPR propio | OpenCV + EasyOCR |
| LPR alternativo | SimpleLPR SDK, dependencia opcional/comercial |
| Integraciones HTTP | requests / clientes específicos por sistema |
| Logging | loguru |
| Testing | pytest |
| HMI/SCADA consumidor | Ignition Perspective |
| Exposición externa opcional | cloudflared o ngrok |

---

## 5. Estructura del proyecto

```text
.
|-- app/
|   |-- main.py                         # Punto de entrada FastAPI
|   |-- core/
|   |   |-- config.py                    # Settings desde .env
|   |   |-- errors.py                    # Excepciones tipadas del dominio
|   |   |-- logging.py                   # Configuración de logs
|   |
|   |-- api/
|   |   |-- dependencies.py              # Inyección de dependencias
|   |   |-- schemas.py                   # Schemas legacy/principales
|   |   |-- integrations_schemas.py      # Schemas para RNTT/Navis/BioStar/Wialon
|   |   |-- routes/
|   |       |-- health_routes.py
|   |       |-- camera_routes.py
|   |       |-- lpr_routes.py               # Endpoints legacy /lpr/*
|   |       |-- lpr_reads_routes.py         # Endpoint formal /api/v1/lpr/reads
|   |       |-- biostar_routes.py
|   |       |-- rntt_routes.py
|   |       |-- crossing_routes.py
|   |       |-- integrations_routes.py
|   |       |-- monitor_routes.py
|   |
|   |-- integrations/
|   |   |-- camera/                      # Providers webcam/RTSP y sesiones OpenCV
|   |   |-- lpr/                         # Engines LPR, SimpleLPR, normalización OCR
|   |   |-- biostar/                     # Cliente/servicio/modelos BioStar
|   |   |-- rntt/                        # Cliente/servicio/modelos RNTT
|   |   |-- navis/                       # Cliente/servicio/modelos Navis
|   |   |-- wialon/                      # Cliente/servicio/modelos Wialon
|   |   |-- ignition/                    # Writer JSON para Ignition
|   |
|   |-- modules/
|       |-- camera/                      # Servicio de cámara y evidencia snapshot
|       |-- lpr/                         # Servicio formal LPR + catálogo dominicano
|       |-- crossing/                    # Reglas de decisión de cruce
|
|-- scripts/
|   |-- poc_supervisor.py               # Supervisor local del PoC
|   |-- monitor_biostar_local.py        # Monitor BioStar local
|   |-- lpr/
|       |-- simplelpr_rtsp_monitor.py    # Monitor continuo SimpleLPR + RTSP
|       |-- requirements-simplelpr.txt
|
|-- config/
|   |-- cameras.example.json            # Plantilla versionada de cámaras
|   |-- cameras.json                    # Config local, no versionar
|
|-- ignition_scripts/                   # Scripts de referencia para Ignition
|-- tests/                              # Pruebas unitarias/integración con mocks
|-- requirements.txt
|-- pytest.ini
|-- README.md
```

---

## 6. Modos de ejecución

### 6.1 API solamente con uvicorn

Este modo levanta solo el backend FastAPI. No inicia monitores continuos.

```powershell
cd C:\intelca\Backend-HGAC
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

URLs locales:

```text
API:     http://localhost:8000
Swagger: http://localhost:8000/docs
Health:  http://localhost:8000/health
```

### 6.2 PoC completo con supervisor

Este modo ejecuta los procesos operativos de la PoC desde una sola consola.

```powershell
cd C:\intelca\Backend-HGAC
.\.venv\Scripts\Activate.ps1
python .\scripts\poc_supervisor.py
```

Procesos esperados del supervisor en la rama final de la PoC:

| Proceso | Función |
|---|---|
| Backend API | Levanta `uvicorn app.main:app` en el host/puerto configurado. |
| BioStar local | Lee eventos del lector local y publica el último evento en JSON. |
| SimpleLPR RTSP | Mantiene abierto el stream RTSP, detecta placa/rótulo y publica el resultado LPR. |
| Wialon cada 5 segundos | Consulta unidades GPS/geocercas y mantiene el estado operativo actualizado para consumo del gate. |

Variables principales del supervisor:

```env
HGAC_START_BACKEND=true
HGAC_START_BIOSTAR=true
HGAC_START_LPR=true
HGAC_RESTART_DELAY_SECONDS=15
HGAC_BACKEND_HOST=127.0.0.1
HGAC_BACKEND_PORT=8000
BIOSTAR_LOCAL_POLL_SECONDS=1
SIMPLELPR_PYTHON=C:/Users/USUARIO/AppData/Local/Programs/Python/Python312/python.exe
```

Nota técnica: en el ZIP revisado, `scripts/poc_supervisor.py` levanta Backend, BioStar y LPR. No se encontró todavía un worker Wialon continuo dentro del supervisor. Si la rama final ya incluye Wialon, documentar también sus variables de control, por ejemplo `HGAC_START_WIALON` y `WIALON_POLL_SECONDS=5`. Si no existe, debe implementarse antes de afirmar que el supervisor mantiene cuatro procesos.

---

## 7. Instalación local

```powershell
# 1. Clonar el repositorio
cd C:\intelca
git clone <URL_DEL_REPOSITORIO>
cd Backend-HGAC

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 4. Instalar dependencias del backend
pip install -r requirements.txt

# 5. Crear archivo de configuración local
copy .env.example .env

# 6. Editar .env con valores reales
notepad .env
```

No subir `.env`, `config/cameras.json`, evidencia, logs ni credenciales al repositorio.

---

## 8. Configuración de cámaras

El backend no debe tener URLs RTSP hardcodeadas. Las cámaras se declaran en `config/cameras.json`, pero la URL real vive en `.env`.

Ejemplo:

```json
{
  "cameras": [
    {
      "camera_id": "CAM-HIT-LPR-01",
      "camera_name": "HIT - LPR Entrada",
      "source_type": "rtsp",
      "source_env": "CAMERA_HIT_LPR_01_RTSP_URL",
      "lpr_roi": {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0
      }
    }
  ]
}
```

En `.env`:

```env
CAMERA_REGISTRY_PATH=./config/cameras.json
CAMERA_HIT_LPR_01_RTSP_URL=rtsp://USER:PASSWORD@172.17.221.113/stream
```

La API no debe devolver credenciales. Los endpoints de status deben exponer fuentes saneadas.

---

## 9. Endpoints principales

### 9.1 Health y documentación

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health` | Healthcheck básico del backend. |
| GET | `/docs` | Swagger UI. |
| GET | `/openapi.json` | Esquema OpenAPI. |

### 9.2 Cámaras

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/v1/cameras/{camera_id}/status` | Estado de la cámara. |
| GET | `/api/v1/cameras/{camera_id}/snapshot.jpg` | Frame JPEG en memoria, diagnóstico. |
| GET | `/api/v1/cameras/{camera_id}/stream.mjpg` | Preview MJPEG para Ignition/navegador. |
| POST | `/api/v1/cameras/{camera_id}/snapshots` | Captura persistente de evidencia. |

### 9.3 LPR

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/v1/lpr/reads` | Lectura formal de placa/rótulo sobre una cámara. |
| POST | `/lpr/read` | Endpoint legacy LPR. |
| POST | `/lpr/debug/snapshot` | Snapshot legacy de depuración. |

Ejemplo:

```powershell
curl -X POST http://localhost:8000/api/v1/lpr/reads ^
  -H "Content-Type: application/json" ^
  -d "{\"camera_id\":\"CAM-HIT-LPR-01\",\"terminal\":\"HainaOccidental\",\"zone\":\"Entrada\",\"access\":\"Gate1\",\"lane\":\"Lane1\",\"event_id\":\"LPR-MANUAL-001\",\"requested_by\":\"ignition\"}"
```

Estados LPR relevantes:

| Estado | Significado |
|---|---|
| `PLATE_DETECTED` | Lectura aceptada por confianza y formato. |
| `LOW_CONFIDENCE` | Hubo candidato, pero no alcanzó confianza mínima. |
| `FORMAT_MISMATCH` | Hubo texto, pero no cumple patrón válido. |
| `AMBIGUOUS_READ` | Dos candidatos son demasiado similares para decidir automáticamente. |
| `NO_PLATE_DETECTED` | No se encontró placa/rótulo útil. |
| `ERROR` | Falla operativa del motor o procesamiento. |

### 9.4 BioStar

| Método | Ruta | Uso |
|---|---|---|
| GET | `/biostar/events/latest` | Último evento publicado por el monitor BioStar local. |
| POST | `/biostar/verify` | Verificación legacy por identificador. |
| GET | `/api/v1/integrations/biostar/devices` | Lista de dispositivos BioStar. |
| POST | `/api/v1/integrations/biostar/events/recent` | Eventos recientes. |
| POST | `/api/v1/integrations/biostar/validate-event` | Valida si un evento permite paso. |

### 9.5 RNTT

| Método | Ruta | Uso |
|---|---|---|
| POST | `/rntt/lookup` | Consulta legacy por placa. |
| POST | `/api/v1/integrations/rntt/query` | Consulta chofer o camión. |
| POST | `/api/v1/integrations/rntt/combined-query` | Consulta combinada chofer/camión por rótulo u otro criterio. |

### 9.6 Navis

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/v1/integrations/navis/query` | Consulta información operacional de truck/driver. |

### 9.7 Wialon

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/v1/integrations/wialon/units` | Resumen de unidades GPS, online status y geocercas. |
| GET | `/api/v1/integrations/wialon/unit/{unit_id_or_name}` | Consulta una unidad por ID, IMEI/unique ID o nombre. |

### 9.8 Decisión de cruce

| Método | Ruta | Uso |
|---|---|---|
| POST | `/crossing/evaluate` | Evalúa el cruce con reglas de negocio. |

---

## 10. Contrato con Ignition

Ignition no debe conectarse directamente a la cámara ni a BioStar/Wialon/RNTT/Navis. Debe consumir el backend.

Patrones actuales:

1. REST directo desde Perspective hacia el backend.
2. Lectura de archivos JSON locales para integraciones temporales.
3. URLs públicas de evidencia bajo `/evidence`.
4. Preview MJPEG en componentes Image de Perspective.

Ejemplo de `Image.props.source` para preview:

```text
{view.custom.backendUrl} + "/api/v1/cameras/" + {view.custom.cameraId} + "/stream.mjpg"
```

Ejemplo de URL de backend en Ignition:

```text
https://<subdominio-cloudflared-o-ngrok>/api/v1/lpr/reads
```

Si Ignition corre en otra máquina o en un gateway remoto, `localhost` no apunta a la PC del backend. En ese caso se debe usar una URL accesible por red, cloudflared o ngrok.

---

## 11. Exponer el backend con cloudflared o ngrok

### 11.1 cloudflared rápido para pruebas

```powershell
cloudflared tunnel --url http://localhost:8000
```

El comando devuelve una URL HTTPS temporal. Esa URL se coloca en Ignition como `backendUrl`.

Ejemplo:

```text
https://example.trycloudflare.com
```

### 11.2 ngrok rápido para pruebas

```powershell
ngrok http 8000
```

Ngrok devuelve una URL HTTPS pública. Esa URL se coloca en Ignition como `backendUrl`.

Ejemplo:

```text
https://example.ngrok-free.app
```

### 11.3 Reglas operativas

- Usar HTTPS para integración externa.
- No exponer Swagger públicamente en entornos reales sin autenticación.
- No compartir `.env` ni URLs RTSP con credenciales.
- Actualizar `EVIDENCE_PUBLIC_BASE_URL` si las evidencias deben abrirse desde Ignition usando la URL pública.
- En Ignition, configurar una sola propiedad base, por ejemplo `backendUrl`, y construir las rutas desde ahí.

Ejemplo:

```env
EVIDENCE_PUBLIC_BASE_URL=https://example.trycloudflare.com/evidence
```

---

## 12. Variables de entorno principales

| Variable | Uso |
|---|---|
| `APP_NAME` | Nombre visible del backend. |
| `APP_ENV` | Entorno: development/staging/production. |
| `LOG_LEVEL` | Nivel de logging. |
| `API_HOST` / `API_PORT` | Host y puerto del API si se usan desde config. |
| `EVIDENCE_BASE_PATH` | Carpeta local para snapshots. |
| `EVIDENCE_PUBLIC_BASE_URL` | Base URL pública para evidencia. |
| `CAMERA_REGISTRY_PATH` | JSON local de cámaras. |
| `CAMERA_*_RTSP_URL` | URLs RTSP reales. Nunca versionar. |
| `LPR_ENGINE` | `opencv_easyocr_poc` o `simplelpr_rd_poc`. |
| `LPR_READ_MIN_CONFIDENCE` | Confianza mínima LPR formal, escala 0-100. |
| `LPR_ENABLE_DOMINICAN_PLATE_CATALOG` | Activa catálogo operativo de patrones dominicanos. |
| `SIMPLELPR_RTSP_URL` | RTSP usado por el monitor continuo SimpleLPR. |
| `SIMPLELPR_CAMERA_ID` | ID lógico de cámara para eventos SimpleLPR. |
| `BIOSTAR_LOCAL_HOST` | Host del lector BioStar local. |
| `BIOSTAR_LOCAL_OUTPUT_PATH` | Archivo JSON del último evento BioStar local. |
| `RNTT_BASE_URL` | Endpoint base RNTT ASMX. |
| `NAVIS_API_BASE` | Endpoint base Navis. |
| `WIALON_HOST` | Host Wialon nube/local. |
| `WIALON_TOKEN` | Token Wialon. No versionar. |
| `IGNITION_LPR_LATEST_PATH` | Archivo JSON latest consumido por Ignition. |
| `IGNITION_EVENT_ENDPOINT` | Endpoint WebDev/HTTP de Ignition, si se usa writer saliente. |

---

## 13. Evidencia y archivos generados

| Ruta | Contenido |
|---|---|
| `evidence/snapshots/` | Snapshots manuales de cámara. |
| `evidence/lpr/frames/` | Frame usado para lectura LPR. |
| `evidence/lpr/crops/` | Recorte de placa/rótulo si hubo detección. |
| `C:/Users/Public/hgac_lpr.json` | Último resultado LPR para Ignition. |
| `C:/Users/Public/hgac_biostar_local.json` | Último evento BioStar local. |
| `data/ignition_outbox/` | Outbox JSON temporal para Ignition. |

Estas rutas son runtime artifacts. No deben versionarse.

---

## 14. Seguridad y manejo de secretos

Reglas mínimas:

- No commitear `.env`.
- No commitear `config/cameras.json` si contiene nombres de variables privadas o configuración local sensible.
- No hardcodear credenciales RTSP, BioStar, RNTT, Navis, Wialon ni tokens de Ignition.
- Sanitizar URLs RTSP antes de devolverlas en responses o logs.
- No exponer Swagger públicamente en un túnel compartido sin control.
- Rotar credenciales si alguna fue subida accidentalmente.
- Mantener `.gitignore` cubriendo `.env`, evidencia, logs, cache, `.venv` y archivos generados.

---

## 15. Tests

Ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

El proyecto incluye pruebas para:

- Healthcheck.
- Reglas de cruce.
- Cámaras y snapshots.
- LPR formal y validadores de placa.
- SimpleLPR con fakes/mocks.
- BioStar local/remoto con mocks.
- RNTT ASMX con mocks.
- Navis con mocks.
- Wialon con mocks.

Las pruebas no deben depender de servicios reales ni de la cámara física.

---

## 16. Decisiones técnicas importantes

- `app/core/config.py` centraliza toda configuración vía `pydantic-settings`.
- `app/core/errors.py` define errores tipados por dominio/integración.
- Cada integración sigue el patrón `client + service + models + factory`.
- La cámara queda abstraída detrás de `CameraService` y `CameraRegistry`.
- La URL RTSP real se resuelve desde `.env`, no desde código ni JSON versionado.
- LPR no decide acceso; solo devuelve observaciones estructuradas.
- Las reglas de cruce viven separadas del IO para poder testearlas.
- Ignition consume el backend por REST/JSON; no accede directamente a los sistemas externos.
- SimpleLPR es una dependencia opcional/comercial y debe convivir con el motor propio OpenCV/EasyOCR.

---

## 17. Roadmap técnico

- [x] Backend FastAPI modular.
- [x] Cámara webcam/RTSP abstraída.
- [x] LPR formal `/api/v1/lpr/reads`.
- [x] Monitor SimpleLPR continuo sobre RTSP.
- [x] BioStar local y remoto.
- [x] RNTT ASMX.
- [x] Navis.
- [x] Wialon por endpoints REST.
- [ ] Confirmar o implementar worker Wialon continuo cada 5 segundos en `poc_supervisor.py`.
- [ ] Persistir eventos y decisiones en base de datos.
- [ ] Reemplazar puente JSON temporal por integración REST completa desde Ignition.
- [ ] Agregar autenticación/autorización al API antes de exponerlo fuera de entorno controlado.
- [ ] Agregar observabilidad: logs estructurados, métricas, health profundo por integración.
- [ ] Definir despliegue productivo con servicio Windows, Docker o systemd según infraestructura final.

---

## 18. Comandos útiles

```powershell
# Activar entorno
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Levantar solo API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Levantar PoC supervisado
python .\scripts\poc_supervisor.py

# Ejecutar monitor SimpleLPR manualmente
python .\scripts\lpr\simplelpr_rtsp_monitor.py

# Ejecutar monitor BioStar manualmente
python .\scripts\monitor_biostar_local.py --poll 1

# Ejecutar tests
pytest -q

# Exponer con cloudflared
cloudflared tunnel --url http://localhost:8000

# Exponer con ngrok
ngrok http 8000
```

---

## 19. Nota de consistencia del repositorio

En el ZIP revisado existen endpoints Wialon y servicio Wialon, pero el archivo `scripts/poc_supervisor.py` aún no muestra un cuarto proceso Wialon continuo. Para evitar documentación falsa, hay dos opciones antes de cerrar la rama:

1. Implementar el worker Wialon en el supervisor y dejarlo con polling de 5 segundos.
2. Mantener el README indicando que Wialon está disponible por endpoint REST, pero no como proceso supervisado continuo.

No se recomienda declarar que el supervisor mantiene cuatro procesos si el código subido todavía solo inicia tres.
