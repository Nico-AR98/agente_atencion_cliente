import os, tempfile
from gtts import gTTS

'''
def generate_voice(text):
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts = gTTS(text=text, lang="es", tld="com.ar")
        tts.save(fp.name)

        os.system(f"mpg123 -q {fp.name}")
'''

def generate_voice(text) -> bytes:
    import io
    buffer = io.BytesIO()
    gTTS(text=text, lang="es", tld="com.ar").write_to_fp(buffer)
    return buffer.getvalue()

    