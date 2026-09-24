import streamlit as st
import asyncio, os
from dotenv import load_dotenv

from ai_models.llm_router import crear_chat
from negocio.utils import calcular_reintegro, recuperar_contrasena
#from speech.voice_generation import generate_voice

load_dotenv()

SYSTEM_ROLE = """
Sos un representante de atención al cliente de una empresa de servicio de
internet. Atendés en español, con un trato amable, empático y breve.

Tenés dos herramientas disponibles y debés usarlas según lo que pida el cliente:

1. calcular_reintegro: usala cuando el cliente reclame un reintegro o una
   compensación por días sin servicio. Necesitás tres datos:
   - dias_sin_servicio: los días que el cliente estuvo sin servicio. Si no los
     menciona, preguntáselos antes de usar la herramienta.
   - indice_malestar: estimalo vos según el tono del mensaje, entre 1.0 y 2.0.
     1.0 = cliente tranquilo, informa el problema sin queja;
     1.3 = molesto pero cordial;
     1.6 = claramente enojado, insiste o reclama con firmeza;
     2.0 = muy enojado: mayúsculas, insultos, amenaza con dar de baja el
     servicio o con hacer un reclamo formal.
   - email: correo electrónico del cliente, para identificarlo y registrar el
     reintegro en el sistema. Si no lo dio, pedíselo antes de usar la
     herramienta.

2. recuperar_contrasena: usala cuando el cliente no pueda entrar a su cuenta,
   haya olvidado la contraseña o pida restablecerla. Necesitás su correo
   electrónico; si no lo dio, pedíselo antes de usar la herramienta. La
   herramienta devuelve un enlace de recuperación (reset_link) que debés
   compartirle al cliente.

Después de usar una herramienta, explicale al cliente el resultado en lenguaje
natural. Si el mensaje no corresponde a ninguna de las dos herramientas,
respondé normalmente como representante de atención al cliente.

Evita incluir "*" en tu respuesta o cualquier caracter especial. Ten en cuenta que todos los valores de las facturas y reintegros por dias sin servicio estan expresados en pesos.
"""

HERRAMIENTAS = [calcular_reintegro, recuperar_contrasena]

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Alexia")

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# --- Interfaz Streamlit ---
st.set_page_config(page_title=ASSISTANT_NAME, page_icon="👩")
st.title(f"👩 {ASSISTANT_NAME}")

# --- Sidebar para opciones
with st.sidebar:
    st.header("Acciones")
    if st.button("Limpiar chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()


#Iniciar la sesión del chat del router
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    st.session_state.chat_session = crear_chat(
        system_role=SYSTEM_ROLE,
        tools=HERRAMIENTAS,
        temperature=0.3
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


#Entrada del usuario:

if prompt := st.chat_input("Escribe tu consulta aqui"):
    # 1: Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    #2: Generamos la respuesta del asistente

    with st.chat_message("assistant"):
        with st.spinner("Procesando ..."):
            try:
                respuesta = run_async(st.session_state.chat_session.enviar_mensaje(prompt))
                st.markdown(respuesta)
                st.session_state.messages.append({"role":"assistant", "content":respuesta})

            except Exception as e:
                st.error(f"Error: {e}")
