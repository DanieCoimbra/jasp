from vosk import Model, KaldiRecognizer
import pyaudio
import json


class SpeechToText:
    def __init__(self, model_path="./models/vosk-model-small-pt-br-0.3"):
        """Inicializa o reconhecimento de voz offline"""
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)

        # Configurar PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000,  # buffer um pouco maior ajuda a evitar overflow [web:145][web:148]
        )
        self.stream.start_stream()

    def listen(self):
        """Escuta contínua e retorna texto quando reconhecido"""
        try:
            while True:
                # IMPORTANTE: exception_on_overflow=False
                data = self.stream.read(4000, exception_on_overflow=False)  # [web:145][web:141]

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    # Estrutura típica: {"text": "frase reconhecida"}
                    text = result.get("text", "").strip()
                    if text:
                        return text

        except KeyboardInterrupt:
            print("Escuta interrompida")
            self.stop()

    def stop(self):
        """Finaliza a escuta"""
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()


# Teste isolado
if __name__ == "__main__":
    stt = SpeechToText()
    print("Escutando... (Ctrl+C para parar)")
    try:
        while True:
            text = stt.listen()
            print(f"Você disse: {text}")
    except KeyboardInterrupt:
        stt.stop()
