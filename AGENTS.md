# AGENTS.md · Portal de solicitudes con IA

## Qué es
Portal donde un cliente (sin perfil técnico) describe un problema o un pedido de cambio. Un asistente con IA le pregunta los datos que faltan, clasifica la solicitud (tipo, severidad, equipo) y la registra.

## Stack
- Python 3.12, **una sola pantalla en Streamlit** (`app.py`), desplegada en Streamlit Community Cloud desde este repo público.
- IA: Gemini con el SDK `google-genai` (`gemini-3.5-flash-lite`, respaldo `gemini-3.8-flash`, timeout 12 s) y Claude con el SDK `anthropic` (`claude-haiku-4-5`) como último respaldo.
- Toda llamada a un modelo pasa por **una sola función**, `consultar_ia(prompt)`, que devuelve `(texto, proveedor)`.
- Memoria del chat en `st.session_state` (`mensajes`, `relato`, `rondas`, `ticket`, `pendiente`).
- Mientras la IA responde, el `chat_input` queda deshabilitado (mensaje en `pendiente`).
- Sin base de datos: el ticket vive en la sesión. La creación está aislada en `crear_ticket()`.

## Reglas
- Las claves (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) **solo** en `st.secrets`. Nunca en el código, el README, los commits ni el chat.
- Leer las claves con `leer_clave()`: la app no se puede romper si no hay secrets.
- Cada llamada a la API va dentro de `try/except` y muestra al usuario un mensaje claro, **sin stack trace ni datos sensibles**.
- El prompt de clasificación pide **solo JSON** con `tipo`, `severidad`, `equipo`, `resumen`, `faltantes`, `es_solicitud` y `mensaje_al_cliente`. Si se cambia el formato, actualizar también la interfaz.
- Las repreguntas salen de `faltantes`, sin una llamada extra a la IA (para ahorrar cuota).
- Máximo `MAX_RONDAS = 3` repreguntas: después se registra igual, marcada con datos pendientes.
- Textos para el usuario en español rioplatense, cordiales y profesionales, cortos. La IA nunca dice que registró o derivó algo si faltan datos.
- **Un cambio por pedido.** Explicar qué se cambió y por qué antes de tocar otra cosa.

## Casos de prueba manuales
1. Ejemplo **"Bot caído"** → Incidente, severidad Crítica o Alta, equipo Agentes e IA.
2. Ejemplo **"Incompleta"** ("No anda.") → el asistente repregunta. Al responder "el bot de WhatsApp, desde ayer" → se crea la solicitud.
3. **Clave de Gemini inválida** con la de Claude válida → responde igual y abajo dice "Clasificado con: Claude".
4. **"hola"** → saludo amable, sin gastar repregunta.
5. **Sin ninguna clave** → mensaje claro en el chat, sin error rojo de Streamlit.

## No hacer sin preguntar
- Cambiar los modelos, agregar dependencias o una base de datos.
- Conectar Azure DevOps u otro sistema externo.
- Hacer push o redesplegar sin avisar.
