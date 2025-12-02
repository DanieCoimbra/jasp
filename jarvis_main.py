#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import time
import re
from speech_to_text import SpeechToText
from language_model import LocalLLM
from neuralTTS import NeuralTTS
#from text_to_speech import TextToSpeech
from arduino_controller import SmartLabController


class JARVIS:
    def __init__(self):
        print("🤖 Inicializando JASP...")
        
        # Módulos
        self.stt = SpeechToText()
        self.llm = LocalLLM(model="mistral")
        #self.tts = TextToSpeech(rate=150)
        self.tts = NeuralTTS(speaker_wav=r"voices\Apresentacao_Com_recepcao.wav")
        self.arduino = SmartLabController()
        
        if not self.arduino.arduino or not self.arduino.arduino.connected:
            print("⚠️ Módulo Arduino indisponível, seguindo só com voz/IA.")
        # Comandos customizados
        self.custom_commands = {
            r"liga.*luz": self.command_light_on,
            r"desliga.*luz": self.command_light_off,
            r"qual.*temperatur": self.command_read_temp,
            r"histórico": self.command_history,
            r"limpar.*histórico": self.command_clear_history,
            r"parar|sair|até logo": self.command_stop,
        }
        
        print("✅ JASP inicializado com sucesso!")
        self.tts.speak_blocking("JASP inicializado. Pronto para começar.")
    
    def process_voice_input(self, text):
        """Processa entrada de voz"""
        print(f"\n📝 Você: {text}")
        
        # Verificar comandos customizados primeiro
        for pattern, handler in self.custom_commands.items():
            if re.search(pattern, text.lower()):
                print(f"🔧 Executando comando customizado...")
                handler(text)
                return True
        
        # Se não for comando customizado, usar LLM
        return False
    
    def run(self):
        """Loop principal"""
        print("\n🎙️ JASP está escutando... (fale 'parar' para sair)")
        print("-" * 50)
        
        try:
            while True:
                # Escutar
                print("\n👂 Escutando...", end=" ", flush=True)
                text = self.stt.listen()
                
                if not text or len(text) < 2:
                    continue
                
                # Processar comando customizado
                if self.process_voice_input(text):
                    continue
                
                # Usar LLM para resposta
                print(f"🤖 JASP está processando...")
                response = self.llm.process_message(text)
                
                
                print(f"🗣️ JASP: {response}")
                
                # Falar resposta
                self.tts.speak_blocking(response)
        
        except KeyboardInterrupt:
            self.shutdown()
    
    # Comandos customizados
    def command_light_on(self, text):
        if not self.arduino or not self.arduino.arduino.connected:
            resp = "Não encontrei o Arduino, não consigo ligar a luz agora."
            print(f"🗣️ JASP: {resp}")
            self.tts.speak_blocking(resp)
            return

        self.arduino.ligar_luz()
        response = "Luz ligada."
        print(f"🗣️ JASP: {response}")
        self.tts.speak_blocking(response)
    
    def command_light_off(self, text):
        if not self.arduino or not self.arduino.arduino.connected:
            resp = "Não encontrei o Arduino, não consigo desligar a luz agora."
            print(f"🗣️ JASP: {resp}")
            self.tts.speak_blocking(resp)
            return
        
        self.arduino.desligar_luz()
        response = "Luz desligada."
        print(f"🗣️ JASP: {response}")
        self.tts.speak_blocking(response)
    
    def command_read_temp(self, text):
        data = self.arduino.leitura_sensor("temperatura")
        if data:
            response = f"A temperatura é {data.get('value', 'desconhecida')} graus."
        else:
            response = "Não consegui ler o sensor."
        print(f"🗣️ JASP: {response}")
        self.tts.speak_blocking(response)
    
    def command_history(self, text):
        history = self.llm.conversation_history
        print(f"\n📋 Histórico ({len(history)} mensagens):")
        for msg in history[-4:]:
            print(f"  {msg['role']}: {msg['content'][:60]}...")
    
    def command_clear_history(self, text):
        self.llm.clear_history()
        response = "Histórico limpo."
        print(f"🗣️ JASP: {response}")
        self.tts.speak_blocking(response)
    
    def command_stop(self, text):
        self.shutdown()
    
    def shutdown(self):
        """Encerramento limpo"""
        print("\n\n👋 Desligando JASP...")
        self.tts.speak_blocking("Até logo!")
        self.stt.stop()
        self.arduino.close()
        exit(0)

if __name__ == "__main__":
    jarvis = JARVIS()
    jarvis.run()