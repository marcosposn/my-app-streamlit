# Especificación · Portal de solicitudes con IA

> Una buena especificación es la que otro asistente de IA podría construir sin haceros preguntas. Esta es la versión final, actualizada con lo aprendido en la prueba.

## 1. Problema y usuario

- **Quién tiene el problema:** una persona de una empresa cliente de una compañía de software que desarrolla agentes conversacionales para clientes de Latinoamérica. Necesita reportar un problema (por ejemplo, un bot que no responde) o pedir un cambio, y no tiene perfil técnico.
- **Cómo lo resuelve hoy:** abre la solicitud en la web de un proveedor externo que no se puede personalizar. Escribe lo que puede, sin guía. Del lado interno, alguien lee cada solicitud, le pide al cliente los datos que faltan, la clasifica y la pasa a mano al sistema interno (Azure DevOps).
- **Qué le molesta de cómo lo hace hoy:** idas y vueltas para completar datos, demora hasta que alguien la mira, solicitudes mal clasificadas y no saber en qué estado está su pedido.
- **Qué parte resuelve la IA:** entender el texto libre, detectar qué datos faltan, repreguntar de forma natural y clasificar por tipo, severidad y equipo. **Queda fuera:** resolver el problema técnico, asignarlo a una persona y abrir el ticket en una herramienta (en esta versión la solicitud no sale de la app).

## 2. Qué hace el producto

1. **Conversación guiada:** el cliente cuenta su problema con sus palabras (o toca un ejemplo) y, si falta algún dato imprescindible, el asistente se lo pregunta, como máximo 3 veces. Un saludo no cuenta como solicitud.
2. **Clasificación automática:** tipo (Incidente / Pedido de cambio / Consulta), severidad (Crítica / Alta / Media / Baja), equipo (Plataforma / Agentes e IA / Integraciones / Reportes / Comercial) y resumen de una frase.
3. **Ficha de la solicitud:** al completarse, muestra la ficha con número y estado. En esta versión el número y el estado existen solo en la sesión: la solicitud no se abre en ninguna herramienta de tickets.

## 3. Entradas y salidas

| El usuario da… | La app devuelve… | Ejemplo |
|---|---|---|
| Un texto libre con su problema | La ficha clasificada | "El bot de WhatsApp de ventas no responde desde ayer a la tarde, a ningún cliente" → Incidente · Crítica · Agentes e IA · SOL-1089 |
| Un texto incompleto | Una repregunta natural | "No anda." → "¿Podrías contarnos exactamente qué es lo que no anda y desde cuándo te pasa…?" |
| La respuesta a la repregunta | Reclasificación con todo lo que contó | "El bot de WhatsApp de ventas no responde desde ayer" → ficha completa |
| Un saludo | Respuesta amable que pide el problema | "hola" → "¡Hola! Contame, ¿en qué te podemos ayudar hoy…?" |

Internamente, el modelo devuelve siempre este JSON:

```json
{"tipo": "Incidente", "severidad": "Crítica", "equipo": "Agentes e IA",
 "resumen": "...", "faltantes": [], "es_solicitud": true, "mensaje_al_cliente": "..."}
```

## 4. La pieza de IA

- **Opción elegida:** API de un LLM: Gemini 3.5 Flash-Lite (principal) y Gemini 3.8 Flash (respaldo), con el SDK `google-genai`. Un tercer nivel con otro proveedor, Claude Haiku 4.5 (SDK `anthropic`), está preparado en el código pero no activado, porque su API es de pago.
- **Por qué:** cada cliente describe su problema a su manera. Un formulario fijo no sabe qué falta en cada caso, y un clasificador zero-shot pone una etiqueta pero no razona qué dato falta ni redacta la repregunta. No hace falta RAG: no se responde desde documentos. Flash-Lite va primero porque en la prueba Flash se colgaba (20,1 s) y Flash-Lite respondía en 0,9–1,0 s con la misma calidad.
- **Instrucciones para el modelo (system prompt):** "Sos un analista de soporte de una empresa de software que recibe solicitudes de clientes. Clasificá la solicitud del cliente. Respondé SOLO con un JSON válido […]. Severidad Crítica solo si el servicio está caído o afecta a todos los usuarios finales. En faltantes poné solo lo imprescindible. es_solicitud es false si el texto es solo un saludo o no tiene sentido. mensaje_al_cliente: tono cordial y profesional, en español rioplatense, sin expresiones muy informales; si faltan datos, preguntá lo que falta en una sola pregunta natural. No inventes acciones: nunca digas que revisaste algo, que lo pasaste al equipo o que ya quedó registrado mientras falten datos. Si hay varios mensajes, no vuelvas a saludar." (texto completo en `app.py`, constante `PROMPT_CLASIFICACION`).

## 5. Flujo del usuario

1. El usuario entra y ve un chat con tres ejemplos: *Bot caído*, *Cambio* e *Incompleta*.
2. Escribe su solicitud o toca un ejemplo. Mientras la IA responde, el chat queda bloqueado ("Esperá la respuesta…").
3. Si falta algo, responde las preguntas del asistente. Al final recibe la ficha de su solicitud y puede empezar otra con **Nueva solicitud**.

## 6. Restricciones

- Coste cero: capa gratuita de la API de Gemini y despliegue gratuito (ruta A). El respaldo de pago (Claude) queda desactivado.
- La clave de la API va en secretos, nunca en el código.
- Sin datos personales reales.
- Lenguaje sencillo, para alguien sin conocimientos técnicos.
- Una sola llamada a la IA por mensaje del cliente, para cuidar la cuota.
- La IA no puede prometer acciones que no ocurrieron.

## 7. Criterios de aceptación

La app está bien si:

| Entrada | Resultado esperado |
|---|---|
| "Desde esta mañana el bot de WhatsApp no responde a nadie" | Incidente, Crítica o Alta, Agentes e IA |
| "Queremos que el asistente salude con el nombre del cliente" | Pedido de cambio, severidad Baja o Media |
| "No anda." | Repregunta qué falla y desde cuándo, sin decir que ya lo registró o derivó |
| Responde a la repregunta con los datos | Reclasifica y muestra la ficha con número (solo en la sesión) |
| Caso límite: "hola" o texto sin sentido | Saludo amable, no gasta repregunta ni crea ficha |
| Caso límite: mensaje de menos de 3 caracteres | Pide que escriba más, sin llamar a la IA |
| Caso límite: no completa tras 3 repreguntas | Muestra la ficha igual, con aviso de "datos pendientes" |
| Caso límite: escribe mientras la IA responde | Chat bloqueado, no se pierde ningún mensaje |
| Error: se acaba la cuota (429) o el modelo no responde en 12 s | Responde el siguiente modelo y lo indica bajo el mensaje |
| Error: ningún modelo disponible o sin claves | "El asistente no está disponible en este momento… volvé a enviar el mensaje". La app no se cae |
| Error: el modelo no devuelve JSON válido | "No pude entender la respuesta del clasificador. Probá de nuevo en unos segundos" |

## 8. Fuera de alcance (por ahora)

- Abrir el ticket en Azure DevOps (vía MCP) y mostrarle al cliente el estado y los comentarios del equipo.
- Activar el respaldo con Claude (requiere una clave de pago de Anthropic).
- Login de clientes, adjuntos e historial entre sesiones.
- Asignar la solicitud a una persona concreta.

## 9. Despliegue

- **Ruta:** A (Streamlit Community Cloud), desde el repositorio público `marcosposn/my-app-streamlit`. Cada commit en `main` redespliega la app.
- **Si trabajáis en equipo (opcional):** trabajo individual.
