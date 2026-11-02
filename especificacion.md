# Especificación · Portal de solicitudes con IA

## 1. Problema y usuario
- **Quién tiene el problema:** una persona de una empresa cliente de una compañía de software (agentes conversacionales para clientes en Latinoamérica) que necesita reportar un problema o pedir un cambio. No tiene perfil técnico.
- **Cómo lo resuelve hoy:** abre la solicitud en la web de un proveedor externo que no se puede personalizar. Escribe lo que puede, sin guía. Del lado interno, alguien lee cada solicitud, le pide por mail los datos que faltan, la clasifica y la pasa a mano al sistema interno (Azure DevOps). El cliente no ve en qué estado está.
- **Qué le frustra:** idas y vueltas para completar datos, demora hasta que alguien la mira y no saber qué pasa con su pedido.
- **Qué parte resuelve la IA:** entender el texto libre, detectar qué datos faltan, repreguntar y clasificar por tipo, severidad y equipo.
- **Qué queda fuera:** resolver el problema, asignar a una persona concreta y la integración real con Azure DevOps (siguiente paso).

## 2. Qué hace el producto
1. Recibe la solicitud en lenguaje natural, en un chat.
2. Clasifica: **tipo** (Incidente / Pedido de cambio / Consulta), **severidad** (Crítica / Alta / Media / Baja) y **equipo** (Plataforma / Agentes e IA / Integraciones / Reportes / Comercial), con un resumen de una frase.
3. Si faltan datos imprescindibles, los pregunta (máximo 3 rondas).
4. Registra la solicitud con un número y estado "Recibida", y la muestra al cliente.

## 3. Entradas y salidas
| Entrada | Salida |
|---|---|
| Texto libre del cliente, por ejemplo "Desde esta mañana el bot de WhatsApp no responde a nadie" | Ficha: tipo, severidad, equipo, resumen y número de solicitud |
| Texto incompleto, por ejemplo "No anda." | Repregunta con la lista de datos que faltan |
| Respuesta del cliente a la repregunta | Reclasificación con todo el relato acumulado |

Salida interna del modelo (JSON):
```json
{"tipo": "Incidente", "severidad": "Crítica", "equipo": "Agentes e IA",
 "resumen": "Bot de WhatsApp sin respuesta desde la mañana", "faltantes": []}
```

## 4. La pieza de IA
- **LLM por API, sin RAG ni entrenamiento:** el problema es interpretar texto libre y razonar qué falta, no buscar en documentos. Un formulario fijo no detecta qué falta porque cada cliente lo cuenta distinto, y un clasificador zero-shot local no puede decir qué dato falta.
- **Gemini 3.5 Flash-Lite** como principal, **Gemini 3.8 Flash** de respaldo y **Claude Haiku 4.5** como respaldo de otro proveedor. La elección se hizo con datos de la prueba: con Flash como principal las respuestas tardaban hasta 20–30 s porque el modelo fallaba o se colgaba, mientras que Flash-Lite respondía en 1–7 s con la misma calidad de clasificación.
- Timeout de 12 s por modelo: si no responde, pasa al siguiente.
- **Un solo prompt** reutilizable para todos los modelos, que exige respuesta en JSON.

## 5. Flujo del usuario
1. Abre la app y ve 3 ejemplos.
2. Escribe su solicitud o toca un ejemplo.
3. Responde las preguntas del asistente, si las hay.
4. Ve su solicitud registrada y puede empezar otra.

## 6. Restricciones
- Coste cero en el uso normal (plan gratuito de Gemini). Claude solo se usa si Gemini falla.
- Claves solo en los Secrets de Streamlit.
- Sin datos personales reales en los ejemplos.
- Lenguaje claro para personas sin perfil técnico.

## 7. Criterios de aceptación
| # | Entrada / situación | Resultado esperado |
|---|---|---|
| 1 | "Desde esta mañana el bot de WhatsApp no responde a nadie" | Incidente, Crítica o Alta, Agentes e IA |
| 2 | "Queremos que el asistente salude con el nombre del cliente" | Pedido de cambio, severidad Baja o Media |
| 3 | "No anda." | Repregunta pidiendo qué falla, desde cuándo y un ejemplo |
| 4 | Responde a la repregunta con los datos | Se reclasifica y se crea la solicitud con número |
| 5 | **Caso límite:** el cliente no completa tras 3 repreguntas | Se registra igual, con el aviso "datos pendientes" |
| 6 | **Caso límite:** mensaje de menos de 3 caracteres | Pide que escriba un poco más, sin llamar a la IA |
| 7 | **Caso límite:** saludo o texto sin sentido ("hola") | Consulta / Baja, y pide que describa el problema |
| 8 | **Error:** cuota de Gemini agotada (429) o modelo colgado | Responde el siguiente modelo y lo indica debajo del mensaje |
| 11 | **Caso límite:** el cliente escribe mientras la IA responde | El chat queda bloqueado ("Esperá la respuesta…"), no se pierde nada |
| 12 | Solicitud incompleta | La IA repregunta sin decir que ya la registró ni que la pasó al equipo |
| 9 | **Error:** ningún modelo disponible o sin claves | Mensaje claro, el texto no se pierde y la app no se cae |
| 10 | **Error:** el modelo devuelve algo que no es JSON | Mensaje "probá de nuevo", la app no se cae |

## 8. Fuera de alcance
- Crear el ticket real en Azure DevOps (vía MCP) y mostrar comentarios del equipo.
- Login de clientes, adjuntos y persistencia entre sesiones.
- Resolver la solicitud o asignarla a una persona concreta.

## 9. Despliegue
Streamlit Community Cloud (ruta A) desde el repositorio público `marcosposn/my-app-streamlit`. Cada commit en `main` redespliega la app.
