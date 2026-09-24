import os
import sys
import contextlib
import speech_recognition as sr

# --- FUNCIÓN PARA SILENCIAR ERRORES DE ALSA/JACK ---
@contextlib.contextmanager
def ignore_stderr():
    """Redirige los errores de la terminal (stderr) al vacío."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    sys.stderr.flush()
    try:
        os.dup2(devnull, sys.stderr.fileno())
        yield
    finally:
        sys.stderr.flush()
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(old_stderr)
        os.close(devnull)

def speech_to_text():
    r = sr.Recognizer()
    
    # Configuraciones para mejorar la detección:
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8  # Menos tiempo de espera para que sea más ágil
    
    # Usamos el silenciador solo durante la apertura del micrófono
    with ignore_stderr():
        try:
            with sr.Microphone() as source:
                print("Ajustando el ruido ambiental...")
                r.adjust_for_ambient_noise(source, duration=1)
                
                print("¡Listo! Podés hablar ahora...")
                # timeout: tiempo máximo esperando a que empiece a hablar
                # phrase_time_limit: tiempo máximo de la frase
                audio = r.listen(source, timeout=10, phrase_time_limit=20)
        except Exception as e:
            print(f"Error al acceder al micrófono: {e}")
            return ""

    try:
        # Usamos Google con el idioma configurado para español de Argentina (u otro)
        texto = r.recognize_google(audio, language="es-AR")
        print(f"Texto reconocido: {texto}")
        return texto
    except sr.UnknownValueError:
        print("No se pudo entender el audio.")
        return ""
    except sr.RequestError as e:
        print(f"Error de conexión con el servicio de Google: {e}")
        return ""
    except Exception as e:
        print(f"Error inesperado: {e}")
        return ""


def transcribir_audio(audio_wav) -> str:
    """Transcribe un audio WAV (bytes o archivo) grabado desde el navegador."""
    r = sr.Recognizer()
    if isinstance(audio_wav, bytes):
        import io
        audio_wav = io.BytesIO(audio_wav)

    with sr.AudioFile(audio_wav) as source:
        audio = r.record(source)

    try:
        return r.recognize_google(audio, language="es-AR")
    except sr.UnknownValueError:
        return ""
