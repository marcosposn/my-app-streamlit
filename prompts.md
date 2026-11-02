# Registro de prompts

Prompts clave usados para construir la app con un asistente de IA (Claude), en orden. Para cada uno: qué pedí, qué hizo la IA y qué revisé o corregí yo.

## 1. Contexto y plan, sin código
> "Tengo que hacer una entrega para el máster [...] Problema: los clientes abren sus solicitudes en una web de un proveedor que no se puede personalizar [...] Qué hará la app: guiar al cliente con una conversación hasta completar la solicitud, clasificarla por tipo, severidad y equipo [...] Pieza de IA: la API de Gemini [...]"

- **IA:** propuso un plan en 9 pasos y sugirió simular Azure DevOps para llegar a la fecha.
- **Yo:** pedí ir **por pasos, sin construir todo de una**, para entender cada parte.

## 2. Seguridad de las claves
> "Pongamos [una] apikey como fallback y que ninguna apikey quede en código público de GitHub."

- **IA:** diseñó el orden de las claves (Secrets → fallback → mensaje sin clave) y propuso el `.gitignore`.

## 3. Fallback a otro proveedor
> "Si tenemos una apikey, ¿cómo le digo a la app que consuma Claude entonces como fallback?"

- **IA:** creó la función única `consultar_ia()` con Gemini primero y Claude después.
- **Yo:** decidí que el resto de la app no sepa qué modelo respondió, salvo una línea informativa.

## 4. Primera pieza de IA (clasificación)
Prompt de la app (en `app.py`, `PROMPT_CLASIFICACION`), reutilizable para cualquier modelo:
> "Sos un analista de soporte [...] Respondé SOLO con un JSON válido [...] tipo, severidad, equipo, resumen, faltantes [...] Severidad Crítica solo si el servicio está caído [...] Si el texto no es una solicitud, usá tipo Consulta [...]"

- **IA:** escribió la app y la probó con la IA simulada.
- **Revisión:** la prueba sin secrets mostró que **la app se caía** (`StreamlitSecretNotFoundError`). Se corrigió con `leer_clave()`.

## 5. Alinear con el curso
> "Estos son los Colab de sesión 3 y 4 [...] serían el paso a paso para construir el trabajo final."

- **IA:** comparó el código con los Colab y **cambió el modelo** por el del curso (`gemini-3.8-flash`, con `gemini-3.5-flash-lite` ante un 429).

## 6. Verificar contra el enunciado
> "¿Pero poner estas claves de esta forma es lo que el profesor pide? ¿Estamos seguros?" / "¿Y en el PDF?"

- **Yo:** no acepté la respuesta sin fuente. Pedí comprobarla en el Colab y en el PDF de la actividad, y ambos coinciden: secretos de la plataforma y nunca en el código.

## 7. Conversación guiada
> "Vamos por ahí, sí" (paso 4: convertir la clasificación en un chat que repregunta)

- **IA:** chat con `session_state`, reclasificación del relato acumulado y tope de 3 repreguntas para evitar un bucle infinito.
- **Yo:** probé en la app desplegada con casos reales ("El bot no funciona, hace dos horas está el sistema caído").

## 8. Prueba en la app desplegada y mejoras
> "Probé el hola" (con captura) / "Me parece que la app no funciona muy bien"

Hallazgos de la prueba, cada uno con su cambio:
- "hola" se trataba como solicitud y gastaba una repregunta → campo `es_solicitud` y respuesta amable.
- La IA inventaba acciones ("ya lo pasé al equipo", "estuve mirando tu caso") → reglas explícitas en el prompt.
- Si el cliente escribía durante "Analizando…", se perdía la respuesta → chat bloqueado mientras responde.
- Tardaba 25–30 s → mostramos modelo y segundos debajo de cada respuesta. **El dato mostró que `gemini-3.8-flash` se colgaba (20,1 s) y siempre respondía el lite (1,3 s)**, así que cambiamos el orden: lite primero. **Resultado: la misma conversación pasó de 20,1 s a 0,9–1,0 s por respuesta.**
- Tono demasiado informal ("Che, qué bajón") → tono cordial y profesional.

## Qué delegué y qué revisé a mano
| Delegué en la IA | Revisé / decidí yo |
|---|---|
| Escribir `app.py`, el prompt y el manejo de errores | El problema, el usuario y el alcance (Azure DevOps queda fuera) |
| Probar los flujos con la IA simulada | Ir paso a paso, y entender cada cambio antes de subirlo |
| Redactar README, AGENTS.md y especificación | Que ninguna clave estuviera en el repo (revisión del código en GitHub) |
| Proponer la cadena de fallback | Que lo de las claves coincidiera con el PDF y el Colab |
| | Prueba en la app desplegada: detecté que "no funciona muy bien" y no di la app por buena hasta medir |
| | Elegir el modelo con el dato medido, no con el que "debería" ser mejor |
