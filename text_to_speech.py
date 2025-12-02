import pyttsx3
import threading


class TextToSpeech:
    def __init__(self, rate=150, volume=0.9):
        """Configurações base e descoberta da voz PT-BR."""
        self.rate = rate
        self.volume = volume
        self.voice_id = None

        # Usa um engine temporário só para descobrir a voz disponível
        tmp_engine = pyttsx3.init('sapi5')
        voices = tmp_engine.getProperty('voices')

        print("Vozes disponíveis:")
        for i, v in enumerate(voices):
            print(i, v.id, v.name, getattr(v, "languages", None))

        for v in voices:
            langs = str(getattr(v, "languages", "")).lower()
            if "pt-br" in langs or "portugu" in v.name.lower() or "pt-br" in v.id.lower():
                self.voice_id = v.id
                print("Usando voz:", v.id)
                break

        if self.voice_id is None:
            print("⚠️ Nenhuma voz PT-BR encontrada, usando voz padrão.")

        tmp_engine.stop()
        del tmp_engine

    def _speak_once(self, text: str):
        """Cria um engine novo, fala o texto e encerra (evita bug de só falar 1 vez)."""
        engine = pyttsx3.init('sapi5')
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)
        if self.voice_id:
            engine.setProperty('voice', self.voice_id)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def speak_blocking(self, text: str):
        """Fala e só volta quando terminar."""
        print("[TTS] Falando:", text)
        self._speak_once(text)

    def speak(self, text: str):
        """Fala em uma thread separada (não bloqueia o fluxo principal)."""
        threading.Thread(target=self._speak_once, args=(text,), daemon=True).start()


if __name__ == "__main__":
    tts = TextToSpeech()

    textos = [
        "Olá! Eu sou JASP, seu assistente de laboratório.",
        "Estou pronto para ajudar com programação e eletrônica!",
        "Como posso ajudá-lo?"
    ]

    for t in textos:
        print("JASP:", t)
        tts.speak_blocking(t)
