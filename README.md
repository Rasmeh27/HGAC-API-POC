# Backend HGAC PoC

Backend de prueba de concepto para control de cruce vehicular portuario en HGAC.
Integra varios subsistemas:

- **LPR** — captura desde cámara (webcam o RTSP) + Plate Recognizer.
- **BioStar 2** — verificación de chofer.
- **RNTT** — consulta del registro nacional vía portal (Selenium aislado; PoC usa stub).
- **Ignition** — temporalmente vía archivos JSON; el backend ya expone REST para consumo futuro.

El objetivo de esta PoC es demostrar el flujo completo de evaluación de cruce
(`AUTHORIZED` / `REJECTED` / `NEEDS_MANUAL_REVIEW`) de forma modular y mantenible.

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py           # Settings cargados desde .env
│   │   ├── errors.py           # Jerarquía de excepciones del dominio
│   │   └── logging.py          # Configuración de loguru
│   ├── api/
│   │   ├── dependencies.py     # Inyección de dependencias
│   │   ├── schemas.py          # Request/Response Pydantic
│   │   └── routes/
│   │       ├── health_routes.py
│   │       ├── lpr_routes.py
│   │       ├── biostar_routes.py
│   │       ├── rntt_routes.py
│   │       └── crossing_routes.py
│   ├── integrations/
│   │   ├── camera/             # CameraProvider + webcam + rtsp
│   │   ├── lpr/                # Cliente Plate Recognizer + servicio
│   │   ├── biostar/            # Cliente BioStar 2 + servicio + modelos
│   │   ├── rntt/               # Cliente RNTT (stub o Selenium) + servicio
│   │   └── ignition/           # IgnitionJsonWriter + modelos
│   └── modules/
│       └── crossing/           # CrossingService + reglas + modelos
└── tests/
    ├── test_health.py
    └── test_crossing_rules.py
```

> **Nota sobre estructura legacy:** En el repositorio existen aún las carpetas
> `apps/` y `src/` del setup inicial. Quedan intactas por compatibilidad pero
> no se usan; el backend oficial vive bajo `app/`.

---

## Requisitos

- Python 3.11 o superior
- Webcam o stream RTSP (para pruebas reales de LPR)
- Token de Plate Recognizer (opcional para PoC; usar stub cuando no esté disponible)
- BioStar 2 accesible por red (opcional para PoC)

---

## Instalación

```powershell
# 1. Clonar (o ubicarse en) el repo
cd C:\intelca\Backend-HGAC

# 2. Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar variables de entorno
copy .env.example .env
# editar .env con valores reales
```

---

## Variables de entorno

Todas viven en `.env`. Las principales:

| Variable | Descripción |
|---|---|
| `APP_ENV` | `development` / `staging` / `production` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` |
| `API_HOST`, `API_PORT` | Host/puerto del servidor |
| `PLATE_RECOGNIZER_API_TOKEN` | Token de Plate Recognizer |
| `CAMERA_PROVIDER` | `webcam` (defecto) o `rtsp` |
| `WEBCAM_INDEX` | Índice de la webcam (0 por defecto) |
| `RTSP_URL` | URL del stream RTSP cuando `CAMERA_PROVIDER=rtsp` |
| `BIOSTAR_HOST`, `BIOSTAR_PORT` | Host BioStar 2 |
| `BIOSTAR_USERNAME`, `BIOSTAR_PASSWORD` | Credenciales BioStar |
| `BIOSTAR_VERIFY_SSL` | `false` para certificados autofirmados |
| `RNTT_USE_STUB` | `true` para usar stub (PoC inicial sin Selenium) |
| `RNTT_PORTAL_URL` | URL del portal RNTT real |
| `IGNITION_JSON_OUTPUT_DIR` | Carpeta donde escribir JSON para Ignition |

El archivo `.env.example` lista la plantilla completa.

---

## Cómo ejecutar

```powershell
# Activar venv si no está activo
.\.venv\Scripts\Activate.ps1

# Levantar el servidor en modo recarga
uvicorn app.main:app --reload
```

El backend queda en `http://localhost:8000`. La documentación interactiva
Swagger está en `http://localhost:8000/docs`.

---

## Endpoints mínimos

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/health` | Healthcheck |
| `POST` | `/lpr/read` | Captura un frame y detecta placa |
| `POST` | `/biostar/verify` | Verifica un usuario por `nombre_o_id` |
| `POST` | `/rntt/lookup` | Consulta una `placa` en RNTT |
| `POST` | `/crossing/evaluate` | Ejecuta el flujo completo y decide |

### Ejemplos rápidos

```bash
# Healthcheck
curl http://localhost:8000/health

# Verificar usuario en BioStar
curl -X POST http://localhost:8000/biostar/verify ^
     -H "Content-Type: application/json" ^
     -d "{\"nombre_o_id\": \"42\"}"

# Consultar placa en RNTT (stub)
curl -X POST http://localhost:8000/rntt/lookup ^
     -H "Content-Type: application/json" ^
     -d "{\"placa\": \"A123456\"}"

# Evaluar cruce
curl -X POST http://localhost:8000/crossing/evaluate ^
     -H "Content-Type: application/json" ^
     -d "{\"gate_id\": \"GATE_01\", \"lane_id\": \"LANE_01\", \"driver_identifier\": \"42\"}"
```

---

## Tests

```powershell
pytest -q
```

Cubre el endpoint `/health` y todas las ramas de las reglas de cruce.

---

## Decisiones de diseño

- **Configuración centralizada en `app/core/config.py`** — un único `Settings`
  con `pydantic-settings`. Nadie más toca `os.environ`.
- **Excepciones del dominio en `app/core/errors.py`** — cada integración
  lanza errores tipados que la capa HTTP mapea a códigos coherentes (502 para
  fallos de upstream, 504 para timeouts, 422 para datos inválidos, etc.).
- **Cada integración tiene `client` + `service` + `models` + `factory`** —
  el cliente solo habla con el sistema externo; el servicio aplica lógica de
  negocio; los modelos exponen tipos limpios; el factory inyecta dependencias.
- **`crossing_rules.evaluate_crossing` es una función pura** — sin IO, sin
  servicios, totalmente testeable sin mocks.
- **Selenium aislado** — la integración RNTT define una interfaz `RnttClient`
  con dos implementaciones (`StubRnttClient` y `SeleniumRnttClient`), así el
  resto del backend nunca importa Selenium directamente.
- **Ignition como puente JSON** — `IgnitionJsonWriter` deja archivos en una
  carpeta configurable; la integración REST nativa queda lista para activarse
  cuando Ignition pueda consumir el API.

---

## Roadmap PoC

- [ ] Portar el script Selenium real al `SeleniumRnttClient`.
- [ ] Integrar Mobotix vía `RtspCameraProvider`.
- [ ] Cambiar puente JSON por consumo REST nativo desde Ignition.
- [ ] Persistir decisiones en SQLite (`data/hgac_poc.db`) para auditoría.
