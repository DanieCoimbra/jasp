# neural_tts.py
from TTS.api import TTS
import torch
from playsound import playsound
import os
import uuid


class NeuralTTS:
    def __init__(self, speaker_wav=r"voices\Apresentacao_Com_recepcao.wav"):
        """
        TTS neural usando XTTS v2 + sua voz como referência.
        O modelo é carregado 1x aqui (vai demorar um pouco na 1ª vez).
        """
        self.speaker_wav = speaker_wav

        # Modelo multilíngue com clonagem de voz (speaker_wav)
        # Coqui XTTS v2 suporta PT-BR e voz de referência. [web:253]
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        if torch.cuda.is_available():
            print("✅ XTTS usando GPU")
            self.tts = self.tts.to("cuda")
        else:
            print("⚠️ XTTS rodando na CPU")

        # Parâmetros básicos
        self.language = "pt"

    def _synthesize_to_file(self, text: str, out_path: str):
        """Gera áudio com a sua voz para um arquivo WAV."""
        self.tts.tts_to_file(
            text=text,
            speaker_wav=self.speaker_wav,
            language=self.language,
            file_path=out_path,
        )

    def speak_blocking(self, text: str):
        """Gera áudio com sua voz e toca (bloqueante, como o antigo speak_blocking)."""
        print("[NeuralTTS] Falando:", text)
        # gera em pasta temp_audio
        rel_path = os.path.join("temp_audio", f"jasp_{uuid.uuid4().hex}.wav")
        os.makedirs(os.path.dirname(rel_path), exist_ok=True)

        # caminho absoluto + normalizado (evita problemas de barra no Windows) [web:301][web:306]
        out_path = os.path.normpath(os.path.abspath(rel_path))

        self._synthesize_to_file(text, out_path)
        playsound(out_path)

        # Opcional: apagar depois
        try:
            os.remove(out_path)
        except OSError:
            pass

    def speak(self, text: str):
        """Interface compatível com a antiga (pode só delegar para blocking)."""
        self.speak_blocking(text)
