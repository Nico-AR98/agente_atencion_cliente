import json, os

from dotenv import load_dotenv

from gemini_assistant import crear_gemini_chat, get_gemini_response
from groq_assistant import get_groq_client, get_groq_config
from hf_assistant import get_hf_response
from ollama_assistant import get_ollama_client, get_ollama_config

load_dotenv()

PROVEEDORES_VALIDOS = ("gemini", "groq", "ollama", "hf")

MAX_ITERACIONES_HERRAMIENTAS = 3

def get_llm_provider():

    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    if provider not in PROVEEDORES_VALIDOS:
        raise ValueError(
            f"LLM_PROVIDER='{provider}' no es válido"
            f"Usá uno de estos: {', '.join(PROVEEDORES_VALIDOS)}"
        )

    return provider


async def _ejecutar_herramienta(tools_por_nombre, nombre, argumentos):
    funcion = tools_por_nombre.get(nombre)

    if funcion in None:
        return {"error": f"La herramienta '{nombre}' no existe."}

    try:
        return await funcion(**argumentos)
    except Exception as error:
        return {"error": str(error)}


class _GeminiChatSession:
    def __init__(self, system_role, tools, temperature, max_output_tokens):
        self._chat = crear_gemini_chat(
            system_role=system_role,
            tools=tools or [],
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )

    async def enviar_mensaje(self, mensaje):
        return await get_gemini_response(system_role=None, prompt=mensaje, chat=self._chat)


class _GroqChatSession:
    def __init__(self, system_role, tools, temperature, max_output_tokens):
        config = get_groq_config()
        self._client = get_groq_client(config)
        self._model = config["model"]
        self._temperature = temperature
        self._max_tokens = max_output_tokens
        self._tools_por_nombre = {fn.__name__: fn for fn in (tools or [])}
        self._tool_schemas = [_esquema_herramienta(fn) for fn in (tools or [])] or None
        self._messages = [{"role": "system", "content": system_role}] if system_role else []

    async def enviar_mensaje(self, mensaje):
        self._messages.append({"role": "user", "content": mensaje})

        for _ in range(MAX_ITERACIONES_HERRAMIENTAS):
            respuesta = await self._client.chat.completions.create(
                model=self._model,
                messages=self._messages,
                tools=self._tool_schemas,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            mensaje_modelo = respuesta.choices[0].message

            if not mensaje_modelo.tool_calls:
                self._messages.append({"role": "assistant", "content": mensaje_modelo.content})
                return mensaje_modelo.content

            self._messages.append(mensaje_modelo.model_dump(exclude_none=True))

            for tool_call in mensaje_modelo.tool_calls:
                argumentos = json.loads(tool_call.function.arguments or "{}")
                resultado = await _ejecutar_herramienta(
                    self._tools_por_nombre, tool_call.function.name, argumentos
                )
                self._messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(resultado, default=str),
                    }
                )

        return "Perdón, no pude resolverlo. ¿Podrías reformular tu pedido?"


def _esquema_herramienta(funcion):
    """Convierte una función Python a un esquema de tool estilo OpenAI/Groq.

    Reutilizamos el generador de esquemas de la librería de Ollama (a partir
    de la firma y el docstring de la función) en vez de escribir uno propio,
    ya que el formato que produce es el mismo que espera Groq.
    """
    from ollama._utils import convert_function_to_tool

    return convert_function_to_tool(funcion).model_dump(exclude_none=True)


class _OllamaChatSession:
    def __init__(self, system_role, tools, temperature, max_output_tokens):
        config = get_ollama_config()
        self._client = get_ollama_client(config)
        self._model = config["model"]
        self._temperature = temperature
        self._max_tokens = max_output_tokens
        self._tools = tools or []
        self._tools_por_nombre = {fn.__name__: fn for fn in self._tools}
        self._messages = [{"role": "system", "content": system_role}] if system_role else []

    async def enviar_mensaje(self, mensaje):
        self._messages.append({"role": "user", "content": mensaje})

        for _ in range(MAX_ITERACIONES_HERRAMIENTAS):
            respuesta = await self._client.chat(
                model=self._model,
                messages=self._messages,
                tools=self._tools or None,
                options={"temperature": self._temperature, "num_predict": self._max_tokens},
            )
            mensaje_modelo = respuesta.message

            if not mensaje_modelo.tool_calls:
                self._messages.append({"role": "assistant", "content": mensaje_modelo.content})
                return mensaje_modelo.content

            self._messages.append(
                {
                    "role": "assistant",
                    "content": mensaje_modelo.content or "",
                    "tool_calls": mensaje_modelo.tool_calls,
                }
            )

            for tool_call in mensaje_modelo.tool_calls:
                resultado = await _ejecutar_herramienta(
                    self._tools_por_nombre,
                    tool_call.function.name,
                    dict(tool_call.function.arguments),
                )
                self._messages.append({"role": "tool", "content": json.dumps(resultado, default=str)})

        return "Perdón, no pude resolverlo. ¿Podrías reformular tu pedido?"


class _HFChatSession:
    def __init__(self, system_role, tools, temperature, max_output_tokens):
        self._system_role = system_role
        self._temperature = temperature
        self._max_tokens = max_output_tokens
        self._history = []

        if tools:
            print(
                "[llm_router] Hugging Face no soporta function calling: "
                "el asistente no va a poder calcular reintegros ni recuperar "
                "contraseñas con este proveedor, solo responder en lenguaje natural."
            )

    async def enviar_mensaje(self, mensaje):
        respuesta = await get_hf_response(
            system_role=self._system_role,
            prompt=mensaje,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            history=self._history,
        )
        self._history.append({"role": "user", "content": mensaje})
        self._history.append({"role": "assistant", "content": respuesta})
        return respuesta


_SESIONES_POR_PROVEEDOR = {
    "gemini": _GeminiChatSession,
    "groq": _GroqChatSession,
    "ollama": _OllamaChatSession,
    "hf": _HFChatSession,
}


def crear_chat(system_role, tools=None, temperature=0.3, max_output_tokens=1024):
    """Crea una sesión de chat con el LLM elegido vía LLM_PROVIDER.

    Devuelve un objeto con un único método, enviar_mensaje(texto) -> str, sin
    importar qué proveedor se haya elegido.
    """
    provider = get_llm_provider()
    sesion_cls = _SESIONES_POR_PROVEEDOR[provider]
    return sesion_cls(system_role, tools, temperature, max_output_tokens)