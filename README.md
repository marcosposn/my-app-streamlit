# 📨 Portal de solicitudes con IA

Portal donde un cliente cuenta con sus palabras qué necesita (un problema o un cambio) y un asistente con IA le pregunta lo que falta, clasifica la solicitud por **tipo, severidad y equipo** y la registra.

- **App desplegada:** https://my-app-app-z24zvysqjc5u44cn39qfvg.streamlit.app/
- **Repositorio:** https://github.com/marcosposn/my-app-streamlit

> Si la app muestra la pantalla "Zzzz", pulsá **"Yes, get this app back up!"** y esperá un minuto: es la suspensión por inactividad del plan gratuito de Streamlit.

## El problema

En una empresa de software que da soporte a clientes de toda Latinoamérica, los clientes abren sus solicitudes en la web de un proveedor externo que no se puede personalizar. Las solicitudes llegan **incompletas o mal clasificadas**, alguien del equipo tiene que pasarlas a mano al sistema interno y el cliente **no ve en qué estado están**.

## Para quién

Una persona de una empresa cliente, sin perfil técnico, que necesita reportar un problema o pedir un cambio.

## Cómo se usa

1. Escribí tu solicitud en el chat, o tocá uno de los ejemplos (*Bot caído*, *Cambio*, *Incompleta*).
2. Si falta algún dato, el asistente te lo pregunta (como máximo 3 veces).
3. Cuando está completa, ves tu solicitud registrada con su número, tipo, severidad, equipo y estado.
4. **Nueva solicitud** para empezar otra.

## La pieza de IA

- **Gemini** (`gemini-3.8-flash`) clasifica y detecta los datos que faltan, devolviendo un JSON.
- Si se agota la cuota o falla, prueba con `gemini-3.5-flash-lite`; si también falla, con **Claude** (`claude-haiku-4-5`).
- Si no responde ningún modelo, la app muestra un mensaje claro y no se cae.

## Estructura

```
app.py              # la app de Streamlit
requirements.txt    # streamlit, google-genai, anthropic
especificacion.md   # qué hace, entradas/salidas, criterios de aceptación
AGENTS.md           # contexto para el agente de programación
prompts.md          # registro de prompts clave
.gitignore          # protege .streamlit/secrets.toml y .env
```

## Ejecutar en local

```bash
pip install -r requirements.txt
# crear .streamlit/secrets.toml con GEMINI_API_KEY (y opcional ANTHROPIC_API_KEY)
streamlit run app.py
```

Las claves **nunca** van en el código: en Streamlit Cloud están en *Settings → Secrets*.

## Siguiente paso

Abrir el ticket en **Azure DevOps** (vía MCP) en lugar de guardarlo en la sesión, y mostrarle al cliente el estado y los comentarios del equipo.
