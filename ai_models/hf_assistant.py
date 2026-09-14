import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()  # Cargamos las variables de entorno desde el archivo .env

def get_hf_config():
    """Obtiene la configuración de Hugging Face desde las variables de entorno.

    Returns:
        dict: Diccionario con la api_key y el modelo a utilizar.
    """
    api_key = os.getenv("API_KEY_HF")
    model = os.getenv("MODEL_HF")

    # Validamos que las variables de entorno estén definidas
    if not api_key:
        raise ValueError("API_KEY_HF no esta seteado en las variables de entorno.")
    if not model:
        raise ValueError("MODEL_HF no esta seteado en las variables de entorno.")

    return {"api_key": api_key, "model": model}


_hf_client = None

def get_hf_client(hf_config=None):
    """Devuelve el cliente de Hugging Face, creándolo una sola vez por proceso."""
    global _hf_client

    if _hf_client is None:
        if hf_config is None:
            hf_config = get_hf_config()
        _hf_client = InferenceClient(token=hf_config["api_key"])

    return _hf_client


def build_messages(system_role, prompt, history=None):
    """Construye la lista de mensajes para enviar a Groq.

    Args:
        system_role (str): Instrucciones del rol del sistema.
        prompt (str): Mensaje del usuario.
        history (list, optional): Historial de mensajes previos. Defaults to None.

    Returns:
        list: Lista de mensajes en el formato esperado por Groq.
    """
    messages = []
    if system_role:
        messages.append({"role": "system", "content": system_role})

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": prompt})
    return messages


def get_hf_response(system_role, prompt, hf_config=None, temperature=0.3, max_tokens=1024, history=None):
    """Obtiene la respuesta de Hugging Face para un mensaje dado.

    Args:
        system_role (str): Instrucciones del rol del sistema.
        prompt (str): Mensaje del usuario.
        hf_config (dict, optional): Configuración de Hugging Face. Defaults to None.
        temperature (float, optional): Controla la creatividad de las respuestas. Defaults to 0.3.
        max_tokens (int, optional): Máximo número de tokens en la respuesta. Defaults to 1024.
        history (list, optional): Historial de mensajes previos. Defaults to None.

    Returns:
        str: Respuesta generada por el modelo de Hugging Face.
    """
    if not prompt.strip():
        raise ValueError("El mensaje no puede estar vacío")

    if hf_config is None:
        hf_config = get_hf_config()

    client = get_hf_client(hf_config)

    try:
        chat_completion = client.chat_completion(
            model=hf_config["model"],
            messages=build_messages(system_role, prompt, history),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error al obtener la respuesta de Hugging Face: {e}"


def main():
    system_role = "Eres un asistente de atención al cliente que ayuda a los usuarios con sus reclamos."
    prompt = "Hola, tengo un problema con mi servicio y quiero un reintegro."
    response = get_hf_response(system_role, prompt)
    print(f"Hugging Face: {response}")


if __name__ == "__main__":
    main()