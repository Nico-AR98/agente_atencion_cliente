import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def get_gemini_config():
    """Obtiene la configuración de Gemini desde las variables de entorno.

    Returns:
        dict: Diccionario con la api_key y el modelo a utilizar.
    """
    api_key = os.getenv("API_KEY_GEMINI")
    model = os.getenv("MODEL_GEMINI")

    # Validamos que las variables de entorno estén definidas
    if not api_key:
        raise ValueError("API_KEY_GEMINI no esta seteado en las variables de entorno.")
    if not model:
        raise ValueError("MODEL_GEMINI no esta seteado en las variables de entorno.")

    return {"api_key": api_key, "model": model}


_gemini_client = None


def get_gemini_client(gemini_config=None):
    """Devuelve el cliente de Gemini, creándolo una sola vez por proceso."""
    global _gemini_client

    if _gemini_client is None:
        if gemini_config is None:
            gemini_config = get_gemini_config()
        _gemini_client = genai.Client(api_key=gemini_config["api_key"])

    return _gemini_client


def build_generate_content_config(system_role, tools, temperature=0.3, max_output_tokens=1024):
    """Construye la configuración para generar contenido con Gemini.

    Args:
        system_role (str): Instrucciones del rol del sistema.
        tools (list): Lista de herramientas disponibles para el modelo.
        temperature (float, optional): Controla la creatividad de las respuestas. Defaults to 0.3.
        max_output_tokens (int, optional): Máximo número de tokens en la respuesta. Defaults to 1024.

    Returns:
        types.GenerateContentConfig: Configuración lista para usar en la llamada a Gemini.
    """
    return types.GenerateContentConfig(
        system_instruction=system_role,
        tools=tools,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def crear_gemini_chat(system_role, tools, temperature=0.3, max_output_tokens=1024, gemini_config=None):
    """Crea la sesión de chat con el rol y las herramientas del agente.

    Usamos un chat (y no una llamada suelta) para que el agente recuerde los
    turnos anteriores: así puede pedir un dato que falta y usarlo después.
    """
    if gemini_config is None:
        gemini_config = get_gemini_config()

    gemini_client = get_gemini_client(gemini_config)

    return gemini_client.chats.create(
        model=gemini_config["model"],
        config=build_generate_content_config(system_role, tools, temperature=temperature, max_output_tokens=max_output_tokens),
    )


def get_gemini_response(system_role, prompt, gemini_config=None, temperature=0.3, max_output_tokens=1024, tools=None, chat=None):   

    try:
        if chat is not None:
            response = chat.send_message(prompt.strip())
        else:
            if gemini_config is None:
                gemini_config = get_gemini_config()

            gemini_client = get_gemini_client(gemini_config)

            response = gemini_client.generate_content(
                model=gemini_config["model"],
                config=build_generate_content_config(system_role, tools, temperature=temperature, max_output_tokens=max_output_tokens),
                contents=prompt.strip()
            )

        return response.text
    except Exception as e:
        return f"Error al obtener la respuesta de Gemini: {e}"

