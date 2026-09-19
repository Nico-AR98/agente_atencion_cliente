
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