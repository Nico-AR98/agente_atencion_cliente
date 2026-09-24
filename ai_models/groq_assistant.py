import os, asyncio
from dotenv import load_dotenv
from groq import AsyncGroq
from ai_models.utils import build_messages

load_dotenv()

def get_groq_config():
    """Obtiene la configuración de Groq desde las variables de entorno.

    Returns:
        dict: Diccionario con la api_key y el modelo a utilizar.
    """
    api_key = os.getenv("API_KEY_GROQ")
    model = os.getenv("MODEL_GROQ")

    # Validamos que las variables de entorno estén definidas
    if not api_key:
        raise ValueError("API_KEY_GROQ no esta seteado en las variables de entorno.")
    if not model:
        raise ValueError("MODEL_GROQ no esta seteado en las variables de entorno.")

    return {"api_key": api_key, "model": model}


_groq_client = None

def get_groq_client(groq_config=None):
    """Devuelve el cliente de Groq, creándolo una sola vez por proceso."""
    global _groq_client

    if _groq_client is None:
        if groq_config is None:
            groq_config = get_groq_config()
        _groq_client = AsyncGroq(api_key=groq_config["api_key"])

    return _groq_client


async def get_groq_response(system_role, prompt, groq_config=None, temperature=0.3, max_tokens=1024, history=None):

    if not prompt.strip():
        raise ValueError("El mensaje no puede estar vacío")

    if groq_config is None:
        groq_config = get_groq_config()

    groq_client = get_groq_client(groq_config)

    try:
        response = await groq_client.chat.completions.create(
            model=groq_config["model"],
            messages=build_messages(system_role, prompt, history),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error al obtener la respuesta de Groq: {e}") from e


async def main():
    system_role = "Eres un asistente de atención al cliente que ayuda a los usuarios con sus reclamos."
    prompt = "Hola, tengo un problema con mi servicio y quiero un reintegro."
    response = await get_groq_response(system_role, prompt)
    print(f"Groq: {response}")


if __name__ == "__main__":
    asyncio.run(main())