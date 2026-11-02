"""Portal de solicitudes de clientes — Paso 3: clasificación con IA.

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
# 3. Interfaz
# ---------------------------------------------------------------------------
EJEMPLOS = {
    "Bot caído": "Desde esta mañana el bot de WhatsApp no responde a nadie, los clientes se están quejando.",
    "Cambio": "Queremos que el asistente salude con el nombre del cliente cuando ya lo conoce.",
    "Incompleta": "No anda.",
}

st.title("📨 Portal de solicitudes")
st.write("Contanos qué necesitás con tus palabras. Nosotros nos encargamos de clasificarlo.")

st.caption("¿No sabés cómo empezar? Probá con un ejemplo:")
cols = st.columns(len(EJEMPLOS))
for col, (nombre, texto) in zip(cols, EJEMPLOS.items()):
    if col.button(nombre, use_container_width=True):
        st.session_state.texto = texto

texto = st.text_area("Tu solicitud", key="texto", height=140,
                     placeholder="Ej.: el reporte mensual no muestra los datos de octubre…")

if st.button("Clasificar solicitud", type="primary"):
    if len(texto.strip()) < 5:
        st.warning("Escribí un poco más para que podamos entender tu solicitud.")
    else:
        with st.spinner("Analizando tu solicitud…"):
            try:
                c, proveedor = clasificar(texto)
            except json.JSONDecodeError:
                st.error("La IA respondió en un formato inesperado. Probá de nuevo en unos segundos.")
            except RuntimeError as e:
                st.error("El servicio de clasificación automática no está disponible ahora. "
                         "Tu solicitud no se perdió: podés volver a intentar en unos minutos.")
                with st.expander("Detalle técnico"):
                    st.code(str(e))
            else:
                a, b, d = st.columns(3)
                a.metric("Tipo", c.get("tipo", "—"))
                b.metric("Severidad", c.get("severidad", "—"))
                d.metric("Equipo", c.get("equipo", "—"))
                st.info(f"**Resumen:** {c.get('resumen', '')}")
                if c.get("faltantes"):
                    st.warning("Para poder ayudarte nos falta:\n\n"
                               + "\n".join(f"- {f}" for f in c["faltantes"]))
                else:
                    st.success("¡Tu solicitud está completa!")
                st.caption(f"Clasificado con: {proveedor}")
