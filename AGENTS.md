# AGENTS.md · Portal de solicitudes con IA

> Este fichero lo leen los agentes de programación antes de tocar el código. Para Claude, `CLAUDE.md` contiene una sola línea que remite aquí.

## Qué es este proyecto

Portal donde un cliente de una empresa de software, sin perfil técnico, cuenta un problema o un pedido de cambio con sus palabras; un asistente con IA le pregunta lo que falta y clasifica la solicitud por tipo, severidad y equipo.

## Cómo está hecho

- Python 3.12.
- Interfaz: Streamlit (ruta A), una sola pantalla con chat (`st.chat_message`, `st.chat_input`) y memoria en `st.session_state` (`mensajes`, `relato`, `rondas`, `ticket`, `pendiente`).
- IA: API de Gemini con el SDK `google-genai`. Los modelos están en la tupla del bucle de `consultar_ia()` en `app.py`: `gemini-3.5-flash-lite` (principal) y `gemini-3.8-flash` (respaldo), con timeout de 12 s. Tercer nivel preparado y no activado: Claude (`claude-haiku-4-5`, SDK `anthropic`), que solo se usa si existe `ANTHROPIC_API_KEY`.
- Toda llamada a un modelo pasa por `consultar_ia(prompt)`, que devuelve `(texto, proveedor)`. El prompt está en la constante `PROMPT_CLASIFICACION`.
- La solicitud vive solo en la sesión: no se abre en ninguna herramienta. La creación está aislada en `crear_ticket()`.
- Archivos: `app.py` (toda la app), `requirements.txt` (dependencias), `README.md`, `especificacion.md` y `prompts.md` (registro de prompts).
- La especificación completa está en [especificacion.md](especificacion.md).

## Reglas

- La clave de la API va SIEMPRE en secretos (`st.secrets`) y se lee con `leer_clave()`, para que la app no se rompa si falta. Nunca en el código, en el README ni en el chat.
- Cada llamada a la API va dentro de `try/except` y muestra un mensaje claro para el usuario, sin detalles técnicos.
- El prompt devuelve SOLO JSON con `tipo`, `severidad`, `equipo`, `resumen`, `faltantes`, `es_solicitud` y `mensaje_al_cliente`. Si cambia el formato, actualizar también la interfaz.
- Una sola llamada a la IA por mensaje: las repreguntas salen del mismo JSON. Máximo `MAX_RONDAS = 3` repreguntas.
- La IA nunca dice que registró, revisó o derivó algo si faltan datos.
- Textos de la interfaz en español rioplatense, cordiales, profesionales y sencillos, pensados para alguien sin conocimientos técnicos.
- Cambios pequeños: uno por petición. Al terminar, explica qué has cambiado y por qué.
- Si añades una librería, añádela también a `requirements.txt` y dilo.
- No uses datos personales reales. Para probar, inventa ejemplos.

## Cómo comprobar que funciona

- Ruta A: `streamlit run app.py` en local (con `.streamlit/secrets.toml`), o haz push y revisa la app en Streamlit Cloud. Debajo de cada respuesta se ve qué modelo respondió y cuánto tardó.
- Casos de prueba (entrada → lo que esperamos):
  1. Ejemplo "Bot caído" → Incidente, Crítica o Alta, Agentes e IA.
  2. "No anda." → repregunta qué falla y desde cuándo; al responder "El bot de WhatsApp de ventas no responde desde ayer" → ficha completa, en ~1 s por respuesta.
  3. "hola" (fuera de tema) → saludo amable que pide el problema, sin gastar repregunta.
  4. App sin claves → mensaje claro en el chat, sin error rojo de Streamlit.

## Qué no hacer

- No borres ni reescribas el README sin preguntar.
- No cambies el modelo ni la arquitectura sin preguntar.
- No conectes Azure DevOps ni otro sistema externo sin preguntar.
- No hagas push ni despliegues sin que yo lo haya revisado.
