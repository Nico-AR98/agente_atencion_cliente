import sys

# PyAudio no tiene wheels para Python 3.14 (compilarlo pide Visual C++).
# PyAudioWPatch es un fork con binarios listos: lo registramos como "pyaudio"
# para que speech_recognition lo encuentre.
try:
    import pyaudio  # noqa: F401
except ImportError:
    import pyaudiowpatch

    sys.modules["pyaudio"] = pyaudiowpatch

import speech_recognition as sr

def speech_to_text():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("Ajustando el ruido ambiental...")
        r.adjust_for_ambient_noise(source)
        print("Listo! Podes hablar ahora.")

        r.pause_threshold = 2

        audio = r.listen(source)

    try:
        texto = r.recognize_google(audio, language="es-ES")
        print(f"Texto reconocido: {texto}")
        return texto

    except Exception as e:
        # Si no se entendio el audio devolvemos "" para que quien llame
        # pueda seguir trabajando con un texto (nunca con None).
        print(f"Ha ocurrido un error: {e}")
        return ""