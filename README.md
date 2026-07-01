# Backend HGAC API

Backend FastAPI para una prueba de concepto de monitoreo y validacion de cruces vehiculares en entorno portuario HGAC/HIT. El sistema integra lectura de placas y rotulos por camara RTSP, eventos BioStar, consultas RNTT/Navis, ubicacion GPS Wialon y consumo desde Ignition Perspective.

> Alcance: PoC operativo local. No debe tratarse como sistema productivo de control de acceso hasta completar persistencia, auditoria, hardening de seguridad, monitoreo de servicios y validaciones oficiales contra las fuentes maestras.

---

## 1. Descripcion del repositorio para GitHub

Usar esta descripcion en el campo **Description** del repositorio:

```text
Backend FastAPI para PoC de monitoreo y validacion de cruces vehiculares portuarios HGAC. Integra LPR RTSP/SimpleLPR, BioStar, RNTT, Navis, Wialon e Ignition mediante APIs REST y puente JSON.
```

Longitud aproximada: 199 caracteres. Esta por debajo del limite de GitHub de 350 caracteres.

---

## 2. Objetivo del proyecto

El backend centraliza las integraciones necesarias para evaluar y monitorear eventos de cruce vehicular en un gate portuario:

- Captura de frames desde webcam o camara IP RTSP.
- Lectura LPR de placas y rotulos dominicanos.
- Publicacion del ultimo resultado LPR para Ignition.
- Lectura de eventos de acceso desde BioStar local/remoto.
- Consulta de chofer/camion en RNTT.
- Consulta de informacion operativa en Navis.
- Consulta de unidades GPS y geocercas en Wialon.
- Exposicion REST para Ignition Perspective y para pruebas manuales desde Swagger.

El objetivo de la PoC es demostrar el flujo completo de observacion y validacion sin acoplar Ignition directamente a las camaras ni a los sistemas externos.

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
        |     |-- Catalogo operativo de patrones dominicanos
        |     |-- Evidencia: frames y crops
        |
        |-- BioStar Integration
        |     |-- BioStar remoto
        |     |-- Monitor local de lector
        |
        |-- RNTT Integration
        |     |-- ASMX / consulta chofer-camion
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

## 4. Stack tecnico

| Capa | Tecnologia |
|---|---|
| API | FastAPI |
| Runtime | Python 3.11+ recomendado |
| Validacion de datos | Pydantic / pydantic-settings |
| Camara | OpenCV, webcam o RTSP |
| LPR propio | OpenCV + EasyOCR |
| LPR alternativo | SimpleLPR SDK, dependencia opcional/comercial |
| Integraciones HTTP | requests / clientes especificos por sistema |
| Logging | loguru |
| Testing | pytest |
| HMI/SCADA consumidor | Ignition Perspective |
| Exposicion externa opcional | cloudflared o ngrok |

---

## 5. Estructura del proyecto

```text
.
|-- app/
|   |-- main.py                         # Punto de entrada FastAPI
|   |-- core/
|   |   |-- config.py                    # Settings desde .env
|   |   |-- errors.py                    # Excepciones tipadas del dominio
|   |   |-- logging.py                   # Configuracion de logs
|   |
|   |-- api/
|   |   |-- dependencies.py              # Inyeccion de dependencias
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
|   |   |-- lpr/                         # Engines LPR, SimpleLPR, normalizacion OCR
|   |   |-- biostar/                     # Cliente/servicio/modelos BioStar
|   |   |-- rntt/                        # Cliente/servicio/modelos RNTT
|   |   |-- navis/                       # Cliente/servicio/modelos Navis
|   |   |-- wialon/                      # Cliente/servicio/modelos Wialon
|   |   |-- ignition/                    # Writer JSON para Ignition
|   |
|   |-- modules/
|       |-- camera/                      # Servicio de camara y evidencia snapshot
|       |-- lpr/                         # Servicio formal LPR + catalogo dominicano
|       |-- crossing/                    # Reglas de decision de cruce
|
|-- scripts/
|   |-- poc_supervisor.py               # Supervisor local del PoC
|   |-- monitor_biostar_local.py        # Monitor BioStar local
|   |-- lpr/
|       |-- simplelpr_rtsp_monitor.py    # Monitor continuo SimpleLPR + RTSP
|       |-- requirements-simplelpr.txt
|
|-- config/
|   |-- cameras.example.json            # Plantilla versionada de camaras
|   |-- cameras.json                    # Config local, no versionar
|
|-- ignition_scripts/                   # Scripts de referencia para Ignition
|-- tests/                              # Pruebas unitarias/integracion con mocks
|-- requirements.txt
|-- pytest.ini
|-- README.md
```

---

## 6. Modos de ejecucion

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

| Proceso | Funcion |
|---|---|
| Backend API | Levanta `uvicorn app.main:app` en el host/puerto configurado. |
| BioStar local | Lee eventos del lector local y publica el ultimo evento en JSON. |
| SimpleLPR RTSP | Mantiene abierto el stream RTSP, detecta placa/rotulo y publica el resultado LPR. |
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

Nota tecnica: en el ZIP revisado, `scripts/poc_supervisor.py` levanta Backend, BioStar y LPR. No se encontro todavia un worker Wialon continuo dentro del supervisor. Si la rama final ya incluye Wialon, documentar tambien sus variables de control, por ejemplo `HGAC_START_WIALON` y `WIALON_POLL_SECONDS=5`. Si no existe, debe implementarse antes de afirmar que el supervisor mantiene cuatro procesos.

---

## 7. Instalacion local

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

# 5. Crear archivo de configuracion local
copy .env.example .env

# 6. Editar .env con valores reales
notepad .env
```

No subir `.env`, `config/cameras.json`, evidencia, logs ni credenciales al repositorio.

---

## 8. Configuracion de camaras

El backend no debe tener URLs RTSP hardcodeadas. Las camaras se declaran en `config/cameras.json`, pero la URL real vive en `.env`.

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

### 9.1 Health y documentacion

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/health` | Healthcheck basico del backend. |
| GET | `/docs` | Swagger UI. |
| GET | `/openapi.json` | Esquema OpenAPI. |

### 9.2 Camaras

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/api/v1/cameras/{camera_id}/status` | Estado de la camara. |
| GET | `/api/v1/cameras/{camera_id}/snapshot.jpg` | Frame JPEG en memoria, diagnostico. |
| GET | `/api/v1/cameras/{camera_id}/stream.mjpg` | Preview MJPEG para Ignition/navegador. |
| POST | `/api/v1/cameras/{camera_id}/snapshots` | Captura persistente de evidencia. |

### 9.3 LPR

| Metodo | Ruta | Uso |
|---|---|---|
| POST | `/api/v1/lpr/reads` | Lectura formal de placa/rotulo sobre una camara. |
| POST | `/lpr/read` | Endpoint legacy LPR. |
| POST | `/lpr/debug/snapshot` | Snapshot legacy de depuracion. |

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
| `LOW_CONFIDENCE` | Hubo candidato, pero no alcanzo confianza minima. |
| `FORMAT_MISMATCH` | Hubo texto, pero no cumple patron valido. |
| `AMBIGUOUS_READ` | Dos candidatos son demasiado similares para decidir automaticamente. |
| `NO_PLATE_DETECTED` | No se encontro placa/rotulo util. |
| `ERROR` | Falla operativa del motor o procesamiento. |

### 9.4 BioStar

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/biostar/events/latest` | Ultimo evento publicado por el monitor BioStar local. |
| POST | `/biostar/verify` | Verificacion legacy por identificador. |
| GET | `/api/v1/integrations/biostar/devices` | Lista de dispositivos BioStar. |
| POST | `/api/v1/integrations/biostar/events/recent` | Eventos recientes. |
| POST | `/api/v1/integrations/biostar/validate-event` | Valida si un evento permite paso. |

### 9.5 RNTT

| Metodo | Ruta | Uso |
|---|---|---|
| POST | `/rntt/lookup` | Consulta legacy por placa. |
| POST | `/api/v1/integrations/rntt/query` | Consulta chofer o camion. |
| POST | `/api/v1/integrations/rntt/combined-query` | Consulta combinada chofer/camion por rotulo u otro criterio. |

### 9.6 Navis

| Metodo | Ruta | Uso |
|---|---|---|
| POST | `/api/v1/integrations/navis/query` | Consulta informacion operacional de truck/driver. |

### 9.7 Wialon

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/api/v1/integrations/wialon/units` | Resumen de unidades GPS, online status y geocercas. |
| GET | `/api/v1/integrations/wialon/unit/{unit_id_or_name}` | Consulta una unidad por ID, IMEI/unique ID o nombre. |

### 9.8 Decision de cruce

| Metodo | Ruta | Uso |
|---|---|---|
| POST | `/crossing/evaluate` | Evalua el cruce con reglas de negocio. |

---

## 10. Contrato con Ignition

Ignition no debe conectarse directamente a la camara ni a BioStar/Wialon/RNTT/Navis. Debe consumir el backend.

Patrones actuales:

1. REST directo desde Perspective hacia el backend.
2. Lectura de archivos JSON locales para integraciones temporales.
3. URLs publicas de evidencia bajo `/evidence`.
4. Preview MJPEG en componentes Image de Perspective.

Ejemplo de `Image.props.source` para preview:

```text
{view.custom.backendUrl} + "/api/v1/cameras/" + {view.custom.cameraId} + "/stream.mjpg"
```

Ejemplo de URL de backend en Ignition:

```text
https://<subdominio-cloudflared-o-ngrok>/api/v1/lpr/reads
```

Si Ignition corre en otra maquina o en un gateway remoto, `localhost` no apunta a la PC del backend. En ese caso se debe usar una URL accesible por red, cloudflared o ngrok.

---

## 11. Exponer el backend con cloudflared o ngrok

### 11.1 cloudflared rapido para pruebas

```powershell
cloudflared tunnel --url http://localhost:8000
```

El comando devuelve una URL HTTPS temporal. Esa URL se coloca en Ignition como `backendUrl`.

Ejemplo:

```text
https://example.trycloudflare.com
```

### 11.2 ngrok rapido para pruebas

```powershell
ngrok http 8000
```

Ngrok devuelve una URL HTTPS publica. Esa URL se coloca en Ignition como `backendUrl`.

Ejemplo:

```text
https://example.ngrok-free.app
```

### 11.3 Reglas operativas

- Usar HTTPS para integracion externa.
- No exponer Swagger publicamente en entornos reales sin autenticacion.
- No compartir `.env` ni URLs RTSP con credenciales.
- Actualizar `EVIDENCE_PUBLIC_BASE_URL` si las evidencias deben abrirse desde Ignition usando la URL publica.
- En Ignition, configurar una sola propiedad base, por ejemplo `backendUrl`, y construir las rutas desde ahi.

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
| `EVIDENCE_PUBLIC_BASE_URL` | Base URL publica para evidencia. |
| `CAMERA_REGISTRY_PATH` | JSON local de camaras. |
| `CAMERA_*_RTSP_URL` | URLs RTSP reales. Nunca versionar. |
| `LPR_ENGINE` | `opencv_easyocr_poc` o `simplelpr_rd_poc`. |
| `LPR_READ_MIN_CONFIDENCE` | Confianza minima LPR formal, escala 0-100. |
| `LPR_ENABLE_DOMINICAN_PLATE_CATALOG` | Activa catalogo operativo de patrones dominicanos. |
| `SIMPLELPR_RTSP_URL` | RTSP usado por el monitor continuo SimpleLPR. |
| `SIMPLELPR_CAMERA_ID` | ID logico de camara para eventos SimpleLPR. |
| `BIOSTAR_LOCAL_HOST` | Host del lector BioStar local. |
| `BIOSTAR_LOCAL_OUTPUT_PATH` | Archivo JSON del ultimo evento BioStar local. |
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
| `evidence/snapshots/` | Snapshots manuales de camara. |
| `evidence/lpr/frames/` | Frame usado para lectura LPR. |
| `evidence/lpr/crops/` | Recorte de placa/rotulo si hubo deteccion. |
| `C:/Users/Public/hgac_lpr.json` | Ultimo resultado LPR para Ignition. |
| `C:/Users/Public/hgac_biostar_local.json` | Ultimo evento BioStar local. |
| `data/ignition_outbox/` | Outbox JSON temporal para Ignition. |

Estas rutas son runtime artifacts. No deben versionarse.

---

## 14. Seguridad y manejo de secretos

Reglas minimas:

- No commitear `.env`.
- No commitear `config/cameras.json` si contiene nombres de variables privadas o configuracion local sensible.
- No hardcodear credenciales RTSP, BioStar, RNTT, Navis, Wialon ni tokens de Ignition.
- Sanitizar URLs RTSP antes de devolverlas en responses o logs.
- No exponer Swagger publicamente en un tunel compartido sin control.
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
- Camaras y snapshots.
- LPR formal y validadores de placa.
- SimpleLPR con fakes/mocks.
- BioStar local/remoto con mocks.
- RNTT ASMX con mocks.
- Navis con mocks.
- Wialon con mocks.

Las pruebas no deben depender de servicios reales ni de la camara fisica.

---

## 16. Decisiones tecnicas importantes

- `app/core/config.py` centraliza toda configuracion via `pydantic-settings`.
- `app/core/errors.py` define errores tipados por dominio/integracion.
- Cada integracion sigue el patron `client + service + models + factory`.
- La camara queda abstraida detras de `CameraService` y `CameraRegistry`.
- La URL RTSP real se resuelve desde `.env`, no desde codigo ni JSON versionado.
- LPR no decide acceso; solo devuelve observaciones estructuradas.
- Las reglas de cruce viven separadas del IO para poder testearlas.
- Ignition consume el backend por REST/JSON; no accede directamente a los sistemas externos.
- SimpleLPR es una dependencia opcional/comercial y debe convivir con el motor propio OpenCV/EasyOCR.

---

## 17. Roadmap tecnico

- [x] Backend FastAPI modular.
- [x] Camara webcam/RTSP abstraida.
- [x] LPR formal `/api/v1/lpr/reads`.
- [x] Monitor SimpleLPR continuo sobre RTSP.
- [x] BioStar local y remoto.
- [x] RNTT ASMX.
- [x] Navis.
- [x] Wialon por endpoints REST.
- [ ] Confirmar o implementar worker Wialon continuo cada 5 segundos en `poc_supervisor.py`.
- [ ] Persistir eventos y decisiones en base de datos.
- [ ] Reemplazar puente JSON temporal por integracion REST completa desde Ignition.
- [ ] Agregar autenticacion/autorizacion al API antes de exponerlo fuera de entorno controlado.
- [ ] Agregar observabilidad: logs estructurados, metricas, health profundo por integracion.
- [ ] Definir despliegue productivo con servicio Windows, Docker o systemd segun infraestructura final.

---

## 18. Comandos utiles

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
