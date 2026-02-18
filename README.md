# 🔍 Sistema de Prospección de Negocios Sin Web

Sistema semiautomático para encontrar negocios en Google Maps que **no tienen página web**, generar mensajes personalizados y enviarlos por WhatsApp.

---

## 📋 Estructura del Proyecto

```
SINPAGINASWEB/
├── main.py                 # 🎯 Script principal (menú interactivo)
├── config.py               # ⚙️ Configuración global
├── scraper_maps.py         # 🔍 Scraper de Google Maps (Playwright)
├── generador_mensajes.py   # ✉️ Generador de mensajes y links wa.me
├── whatsapp_sender.py      # 📤 Envío masivo via WhatsApp Web
├── exportador.py           # 💾 Exportación a CSV/Excel
├── requirements.txt        # 📦 Dependencias Python
├── setup.sh                # 🔧 Script de instalación
└── README.md               # 📖 Este archivo
```

---

## 🚀 Instalación Rápida

### Opción 1: Script automático (Linux)
```bash
cd ~/Escritorio/SINPAGINASWEB
chmod +x setup.sh
./setup.sh
```

### Opción 2: Manual
```bash
cd ~/Escritorio/SINPAGINASWEB

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegador Chromium para Playwright
playwright install chromium
playwright install-deps chromium
```

---

## ▶️ Cómo Usar

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar el sistema
python3 main.py
```

### Menú Principal:
1. **Buscar negocios** — Abre Google Maps, busca por término, filtra los que NO tienen web
2. **Cargar CSV** — Carga prospectos desde un archivo anterior
3. **Enviar por WhatsApp** — Envío masivo con pausas inteligentes anti-bloqueo
4. **Ver prospectos** — Muestra la lista actual en memoria
5. **Generar links** — Genera links wa.me para envío manual
6. **Configuración** — Ver/cambiar parámetros

---

## 🛡️ Sistema Anti-Bloqueo

El sistema incluye múltiples capas de protección:

| Protección | Detalle |
|------------|---------|
| **Pausas aleatorias** | 45-120 segundos entre cada mensaje |
| **Pausa larga** | 5-10 minutos cada 5 mensajes |
| **Límite por sesión** | Máximo 20 mensajes por sesión |
| **Detección de bloqueo** | Detecta textos de restricción y se pausa automáticamente |
| **Verificación de vinculación** | Verifica que WhatsApp Web esté conectado antes de enviar |
| **Re-verificación** | Cada 3 mensajes verifica que siga vinculado |

---

## ⚙️ Configuración

Edita `config.py` para personalizar:

- **`CODIGO_PAIS`**: Tu código de país (por defecto: `591` Bolivia)
- **`PLANTILLA_MENSAJE`**: El mensaje que se enviará
- **`PAUSA_MIN / PAUSA_MAX`**: Tiempos de espera del scraper
- **`ARCHIVO_CSV / ARCHIVO_EXCEL`**: Nombres de los archivos de salida

---

## 📱 Flujo de WhatsApp Web

1. El sistema abre WhatsApp Web en un navegador
2. Te pide escanear el código QR con tu teléfono
3. Verifica automáticamente que la vinculación sea exitosa
4. Confirma la conexión antes de empezar a enviar
5. Envía mensajes con pausas humanas
6. Si detecta bloqueo, se pausa automáticamente (1 hora)
7. Al terminar, guarda el estado de cada envío en CSV/Excel

---

## ⚠️ Advertencias Importantes

- **No abuses del envío masivo.** WhatsApp puede bloquear tu número permanentemente.
- **Usa un número secundario** para las pruebas iniciales.
- **El modo semiautomático (Opción 5: links)** es más seguro porque tú controlas cada envío.
- **Google Maps** puede bloquear tu IP si haces muchas búsquedas seguidas. Usa VPN si es necesario.

---

## 📊 Archivos Generados

- `prospectos.csv` — Datos de todos los negocios encontrados
- `prospectos.xlsx` — Mismo contenido en formato Excel
- `whatsapp_session/` — Datos de sesión de WhatsApp Web (no borrar si quieres mantener la vinculación)
