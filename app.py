"""Portal de solicitudes de clientes — Paso 4: conversación guiada hasta completar la solicitud.

El cliente describe su problema con sus palabras y la IA devuelve:
tipo, severidad, equipo, un resumen y qué datos faltan.
Proveedores: Gemini (principal) -> Claude (fallback). Las claves van en st.secrets.
"""

import json

import streamlit as st

st.set_page_config(page_title="Portal de solicitudes", page_icon="📨")

# ---------------------------------------------------------------------------
# 1. Prompt de clasificación (reutilizable: mismo texto para los dos modelos)
# ---------------------------------------------------------------------------
PROMPT_CLASIFICACION = """Sos un analista de soporte de una empresa de software que recibe
solicitudes de clientes. Clasificá la solicitud del cliente.

Respondé SOLO con un JSON válido, sin texto extra ni ```, con esta forma exacta:
{{
  "tipo": "Incidente" | "Pedido de cambio" | "Consulta",
  "severidad": "Crítica" | "Alta" | "Media" | "Baja",
  "equipo": "Plataforma" | "Agentes e IA" | "Integraciones" | "Reportes" | "Comercial",
  "resumen": "una frase de máximo 20 palabras",
  "faltantes": ["dato que falta para poder actuar", "..."]
}}

Reglas:
- Severidad Crítica solo si el servicio está caído o afecta a todos los usuarios finales.
- En "faltantes" poné solo lo imprescindible (por ejemplo: desde cuándo pasa,
  qué agente o bot, un ejemplo concreto, impacto). Lista vacía si no falta nada.
- Si el texto no es una solicitud (saludo, texto sin sentido), usá tipo "Consulta",
  severidad "Baja" y en faltantes pedí que describa el problema.

Solicitud del cliente:
\"\"\"{texto}\"\"\"
"""

# ---------------------------------------------------------------------------
# 2. Llamada a la IA con fallback Gemini -> Claude
# ---------------------------------------------------------------------------
def leer_clave(nombre: str) -> str | None:
    """Lee una clave de st.secrets sin romper la app si no hay secrets configurados."""
    try:
        return st.secrets.get(nombre)
    except Exception:
        return None


def consultar_ia(prompt: str) -> tuple[str, str]:
    """Devuelve (respuesta, proveedor). Prueba Gemini y, si falla, Claude."""
    errores = []

    if clave := leer_clave("GEMINI_API_KEY"):
        from google import genai

        # Modelos del curso: si el principal da 429 (cuota) o 503, probamos el "lite"
        for modelo in ("gemini-3.8-flash", "gemini-3.5-flash-lite"):
            try:
                cliente = genai.Client(api_key=clave)
                r = cliente.models.generate_content(model=modelo, contents=prompt)
                if r.text:
                    return r.text, f"Gemini ({modelo})"
            except Exception as e:  # cuota agotada, clave inválida, red...
                errores.append(f"{modelo}: {e}")

    if clave := leer_clave("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            cliente = anthropic.Anthropic(api_key=clave)
            r = cliente.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.content[0].text, "Claude"
        except Exception as e:
            errores.append(f"Claude: {e}")

    raise RuntimeError(" | ".join(errores) or "No hay ninguna API key configurada.")


def clasificar(texto: str) -> tuple[dict, str]:
    """Clasifica la solicitud. Devuelve (clasificación, proveedor)."""
    respuesta, proveedor = consultar_ia(PROMPT_CLASIFICACION.format(texto=texto))
    limpio = respuesta.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(limpio), proveedor



# ---------------------------------------------------------------------------
# 3. Conversación: memoria en session_state (Streamlit reejecuta el script en cada clic)
# ---------------------------------------------------------------------------
MAX_RONDAS = 3  # como máximo 3 repreguntas: después se crea la solicitud igual (no queremos un bucle infinito)

EJEMPLOS = {
    "Bot caído": "Desde esta mañana el bot de WhatsApp no responde a nadie, los clientes se están quejando.",
    "Cambio": "Queremos que el asistente salude con el nombre del cliente cuando ya lo conoce.",
    "Incompleta": "No anda.",
}


def reiniciar():
    st.session_state.mensajes = []      # lo que se ve en el chat
    st.session_state.relato = ""        # todo lo que contó el cliente, acumulado
    st.session_state.rondas = 0
    st.session_state.ticket = None


if "mensajes" not in st.session_state:
    reiniciar()


def decir(rol: str, texto: str):
    st.session_state.mensajes.append({"role": rol, "content": texto})


def crear_ticket(c: dict, proveedor: str, incompleta: bool):
    """Por ahora el ticket queda en la sesión. Siguiente paso: abrirlo en Azure DevOps."""
    numero = f"SOL-{1000 + len(st.session_state.relato) % 9000}"
    st.session_state.ticket = {**c, "numero": numero, "proveedor": proveedor,
                               "estado": "Recibida", "incompleta": incompleta}


def procesar(mensaje: str):
    """Suma el mensaje al relato, reclasifica y decide: repreguntar o crear la solicitud."""
    decir("user", mensaje)
    st.session_state.relato += ("\n" if st.session_state.relato else "") + mensaje

    try:
        c, proveedor = clasificar(st.session_state.relato)
    except json.JSONDecodeError:
        decir("assistant", "⚠️ No pude entender la respuesta del clasificador. "
                           "Probá enviar tu mensaje de nuevo en unos segundos.")
        return
    except RuntimeError:
        decir("assistant", "⚠️ El asistente no está disponible en este momento "
                           "(puede ser un límite de uso del servicio). Lo que escribiste no se perdió: "
                           "esperá un minuto y volvé a enviar el mensaje.")
        return

    faltantes = c.get("faltantes") or []
    if faltantes and st.session_state.rondas < MAX_RONDAS:
        st.session_state.rondas += 1
        decir("assistant",
              f"Entendido: **{c.get('resumen', '')}**\n\n"
              "Para que el equipo pueda resolverlo rápido, ¿me contás también…?\n\n"
              + "\n".join(f"- {f}" for f in faltantes))
    else:
        crear_ticket(c, proveedor, incompleta=bool(faltantes))
        decir("assistant", "¡Listo! Ya registré tu solicitud. Abajo tenés el detalle.")


# ---------------------------------------------------------------------------
# 4. Interfaz
# ---------------------------------------------------------------------------
st.title("📨 Portal de solicitudes")
st.write("Contanos qué necesitás con tus palabras. Si falta algún dato, te lo preguntamos.")

# Ejemplos solo al principio, para que un usuario nuevo sepa cómo arrancar
ejemplo = None
if not st.session_state.mensajes:
    st.caption("¿No sabés cómo empezar? Probá con un ejemplo:")
    for col, (nombre, texto) in zip(st.columns(len(EJEMPLOS)), EJEMPLOS.items()):
        if col.button(nombre, use_container_width=True):
            ejemplo = texto

for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

t = st.session_state.ticket
if t:
    with st.container(border=True):
        st.subheader(f"Solicitud {t['numero']} · {t['estado']}")
        a, b, d = st.columns(3)
        a.metric("Tipo", t.get("tipo", "—"))
        b.metric("Severidad", t.get("severidad", "—"))
        d.metric("Equipo", t.get("equipo", "—"))
        st.info(f"**Resumen:** {t.get('resumen', '')}")
        if t["incompleta"]:
            st.warning("Se registró con datos pendientes: el equipo puede contactarte para completarla.")
        st.caption(f"Clasificado con: {t['proveedor']}")
    if st.button("Nueva solicitud"):
        reiniciar()
        st.rerun()
else:
    entrada = st.chat_input("Escribí tu solicitud o tu respuesta…")
    mensaje = ejemplo or entrada
    if mensaje:
        if len(mensaje.strip()) < 3:
            decir("assistant", "Escribí un poco más para que pueda entender qué necesitás.")
        else:
            with st.spinner("Analizando…"):
                procesar(mensaje.strip())
        st.rerun()
