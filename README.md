# 🤖 Telegram Leads Bot

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Airtable](https://img.shields.io/badge/Airtable-Database-18BFFF?style=for-the-badge&logo=airtable&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-AI-D97757?style=for-the-badge&logo=anthropic&logoColor=white)

Bot de Telegram para captura y gestión automática de leads con inteligencia artificial. Extrae datos de los usuarios en lenguaje natural, los almacena en Airtable y presenta un menú interactivo de opciones.

---

## 🔄 Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO DEL BOT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Usuario abre el chat                                          │
│         │                                                        │
│         ▼                                                        │
│   Presiona /start  ──────────────────────────────────────────►  │
│                                                         Bot      │
│                                                    "¡Hola! 👋   │
│                                                Necesito tu       │
│                                            nombre, email         │
│                                            y celular"            │
│         │                                                        │
│         ▼                                                        │
│   Usuario escribe en lenguaje natural                           │
│   "Soy Rod, correo rod@gmail.com, cel +52 55 1234"             │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────┐                                               │
│   │  Claude AI  │  Extrae: name / email / phone                 │
│   └─────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│   ┌─────────────┐                                               │
│   │  Airtable   │  Guarda el registro con Owner automático      │
│   └─────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│   Bot muestra menú interactivo                                  │
│                                                                  │
│   ┌──────────────────────┐                                      │
│   │ 🚀 KanbanPRO (Free) │ ──► Mensaje: "En breve recibirás     │
│   └──────────────────────┘          un correo con los detalles" │
│   ┌──────────────────────┐                                      │
│   │ 🎁 Mis Regalos       │ ──► Enlace directo a recursos        │
│   └──────────────────────┘                                      │
│   ┌──────────────────────┐                                      │
│   │ 🛠 Soporte/Consultas │ ──► Enlace a FAQ                     │
│   └──────────────────────┘                                      │
│         │                                                        │
│         ▼                                                        │
│   Airtable actualiza "option selected"                          │
│   → Dispara automatización de correo                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Stack Tecnológico

| Componente | Tecnología | Función |
|---|---|---|
| Bot | `python-telegram-bot` | Interfaz con Telegram |
| IA | `anthropic` (Claude Sonnet) | Extracción de datos en lenguaje natural |
| Base de datos | `pyairtable` + Airtable | Almacenamiento de leads |
| Config | `python-dotenv` | Gestión de credenciales |

---

## 🗃️ Estructura de Airtable

La tabla de leads requiere las siguientes columnas:

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Single line text | Nombre del lead |
| `email` | Email | Correo del lead |
| `phone` | Phone number | Celular del lead |
| `option selected` | Single line text | Botón que eligió |
| `Owner` | Email | Siempre `roesinf2@gmail.com` (dispara automatización) |

---

## 🚀 Instalación

**1. Clona el repositorio**
```bash
git clone https://github.com/RodrigoInfante48/Telegram.git
cd Telegram
```

**2. Instala dependencias**
```bash
pip install python-telegram-bot anthropic pyairtable python-dotenv
```

**3. Crea el archivo `.env`**
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
ANTHROPIC_API_KEY=tu_api_key_aqui
AIRTABLE_API_KEY=tu_pat_aqui
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_TABLE_NAME=nombre_o_id_de_tabla
```

| Variable | Dónde obtenerla |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/botfather) en Telegram |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `AIRTABLE_API_KEY` | Airtable → Account → Personal Access Tokens |
| `AIRTABLE_BASE_ID` | URL de tu base: `airtable.com/appXXXXXX/...` |

> **Permisos requeridos en el token de Airtable:** `data.records:read`, `data.records:write`, `schema.bases:read`

**4. Ejecuta el bot**
```bash
python main.py
```

---

## 📁 Estructura del proyecto

```
Telegram/
├── main.py          # Lógica completa del bot
├── .env             # Credenciales (no incluido en el repo)
├── .gitignore       # Excluye .env y archivos de Python
└── README.md        # Este archivo
```

---

## 💡 Características clave

- **Lenguaje natural** — El usuario puede escribir sus datos como quiera. Claude AI los interpreta y extrae nombre, email y teléfono automáticamente.
- **Re-entrada** — El usuario puede iniciar el flujo con `/start` en cualquier momento, sin importar el estado anterior.
- **Trazabilidad** — Cada lead queda registrado en Airtable con la opción que seleccionó, lo que permite disparar automatizaciones de email específicas por segmento.
- **Una sola instancia** — Para evitar conflictos, siempre detener el proceso anterior antes de iniciar uno nuevo.

---

## ⚠️ Importante

- **Nunca subas el archivo `.env`** a GitHub. Está protegido por `.gitignore`.
- Para producción, considera desplegar el bot en un servidor (Railway, Render, VPS) para que corra 24/7.
- Si necesitas reiniciar el bot en Windows: `taskkill /F /IM python.exe`
