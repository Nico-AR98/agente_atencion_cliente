"""Agente de atención al cliente (reclamos) con Gemini y function calling.

Toma como guía la estructura de assistant2.py (bucle de conversación por
consola) y de gemini_assistant.py (configuración y llamada al modelo).

En función del mensaje que el usuario envíe, el agente decide si debe:
    - calcular un reintegro por días sin servicio,
    - iniciar el recupero de contraseña, o
    - simplemente responder como representante de atención al cliente.

Variables de entorno (archivo .env):
    API_KEY_GEMINI    clave de la API de Gemini (obligatoria).
    MODEL_GEMINI      modelo a usar (obligatoria).
    ASSISTANT_NAME    nombre del asistente (opcional).
"""

import os

from dotenv import load_dotenv
from ai_models.gemini_assistant import get_gemini_response, crear_gemini_chat
from negocio.utils import calcular_reintegro, recuperar_contrasena
from speech.sp_recognition import speech_to_text
from speech.voice_generation import generate_voice


load_dotenv()  # Cargamos las variables de entorno desde el archivo .env


# Palabras con las que el usuario puede terminar la conversación.
SALIDAS = {"salir", "exit", "quit", "chau"}

# Rol del sistema: define el comportamiento del agente y cómo debe estimar el
# índice de malestar a partir de la forma en que se expresa el cliente.
SYSTEM_ROLE = """
Sos un representante de atención al cliente de una empresa de servicio de
internet. Atendés en español, con un trato amable, empático y breve.

Tenés dos herramientas disponibles y debés usarlas según lo que pida el cliente:

1. calcular_reintegro: usala cuando el cliente reclame un reintegro o una
   compensación por días sin servicio. Necesitás dos datos:
   - dias_sin_servicio: los días que el cliente estuvo sin servicio. Si no los
     menciona, preguntáselos antes de usar la herramienta.
   - indice_malestar: estimalo vos según el tono del mensaje, entre 1.0 y 2.0.
     1.0 = cliente tranquilo, informa el problema sin queja;
     1.3 = molesto pero cordial;
     1.6 = claramente enojado, insiste o reclama con firmeza;
     2.0 = muy enojado: mayúsculas, insultos, amenaza con dar de baja el
     servicio o con hacer un reclamo formal.

2. recuperar_contrasena: usala cuando el cliente no pueda entrar a su cuenta,
   haya olvidado la contraseña o pida restablecerla. Necesitás su correo
   electrónico; si no lo dio, pedíselo antes de usar la herramienta.

Después de usar una herramienta, explicale al cliente el resultado en lenguaje
natural. Si el mensaje no corresponde a ninguna de las dos herramientas,
respondé normalmente como representante de atención al cliente.
"""



# --------------------------------------------------------------------------- #
# Herramientas: funciones que el modelo puede invocar
# --------------------------------------------------------------------------- #



# Herramientas que se le pasan al modelo. Gemini las invoca automáticamente
# cuando el mensaje del usuario lo requiere (automatic function calling).
HERRAMIENTAS = [calcular_reintegro, recuperar_contrasena]


# --------------------------------------------------------------------------- #
# Agente
# --------------------------------------------------------------------------- #

# El cliente se guarda a nivel de módulo: si fuera una variable local, Python
# lo destruiría al salir de la función y cerraría la conexión con la API.



def atender_reclamo(chat, mensaje):
   return get_gemini_response(system_role=SYSTEM_ROLE, prompt=mensaje, chat=chat)


def get_user_input():
    """Solicita un mensaje al usuario."""
    return input("Cliente: ")


def main():
    assistant_name = os.getenv("ASSISTANT_NAME", "Atención al Cliente")
    chat = crear_gemini_chat(system_role=SYSTEM_ROLE, tools=HERRAMIENTAS, temperature=0.3, max_output_tokens=1024)

    #print(f"{assistant_name}: ¡Hola! ¿En qué puedo ayudarte hoy?")
    mensaje_inicial = "¡Hola! ¿En qué puedo ayudarte hoy?"
    print(f"{assistant_name}: {mensaje_inicial}")
    print("(escribí 'salir' para terminar)\n")

    generate_voice(mensaje_inicial)

    while True:
        try:
            mensaje = (speech_to_text() or "").strip()

            if not mensaje:
                # No se reconocio nada: volvemos a escuchar.
                continue

            if mensaje.lower() in SALIDAS:
                break

            respuesta = atender_reclamo(chat, mensaje)
            print(f"{assistant_name}: {respuesta}\n")
            generate_voice(respuesta)

        except (KeyboardInterrupt, EOFError):
            print(f"\n{assistant_name}: sesión finalizada.")
            break
        except Exception as error:
            # El programa no se detiene: informa el error y sigue atendiendo.
            print(f"Error controlado: {error}\n")

    print(f"{assistant_name}: Gracias por comunicarte. ¡Hasta luego!")


if __name__ == "__main__":
    main()
