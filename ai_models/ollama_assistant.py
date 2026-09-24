import os, asyncio
from dotenv import load_dotenv
from ollama import AsyncClient
from ai_models.utils import build_messages

load_dotenv()

def get_ollama_config():
    """Obtiene la configuración de Ollama desde las variables de entorno.

    Returns:
        dict: Diccionario con la api_key y el modelo a utilizar.
    """
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("MODEL_OLLAMA")

    # Validamos que las variables de entorno estén definidas
    if not host:
        raise ValueError("OLLAMA_HOST no esta seteado en las variables de entorno.")
    if not model:
        raise ValueError("MODEL_HF no esta seteado en las variables de entorno.")

    return {"host": host, "model": model}


_ollama_client = None

def get_ollama_client(ollama_config=None):
    """Devuelve el cliente de Ollama, creándolo una sola vez por proceso."""
    global _ollama_client

    if _ollama_client is None:
        if ollama_config is None:
            ollama_config = get_ollama_config()
        _ollama_client = AsyncClient(host=ollama_config["host"])

    return _ollama_client


async def get_ollama_response(system_role, prompt,ollama_config=None, temperature=0.3, max_tokens=1024, history=None):
    """Obtiene la respuesta de Ollama para un mensaje dado.

    Args:
        system_role (str): Instrucciones del rol del sistema.
        prompt (str): Mensaje del usuario.
        ollama_config (dict, optional): Configuración de Ollama. Defaults to None.
        temperature (float, optional): Controla la creatividad de las respuestas. Defaults to 0.3.
        max_tokens (int, optional): Máximo número de tokens en la respuesta. Defaults to 1024.
        history (list, optional): Historial de mensajes previos. Defaults to None.

    Returns:
        str: Respuesta generada por el modelo de Ollama.
    """
    if not prompt.strip():
        raise ValueError("El mensaje no puede estar vacío")

    if ollama_config is None:
        ollama_config = get_ollama_config()

    client = get_ollama_client(ollama_config)

    try:
        response = await client.chat(
            model=ollama_config["model"],
            messages=build_messages(system_role, prompt, history),
            options = {"temperature": temperature, "max_tokens": max_tokens}
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error al obtener la respuesta de Ollama: {e}"


async def main():
    system_role = "Eres un asistente de atención al cliente que ayuda a los usuarios con sus reclamos."
    prompt = "Hola, tengo un problema con mi servicio y quiero un reintegro."
    response = await get_ollama_response(system_role, prompt)
    print(f"Ollama: {response}")


if __name__ == "__main__":
    asyncio.run(main())