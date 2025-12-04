#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import time
import re
from speech_to_text import SpeechToText
from language_model import LocalLLM
from neuralTTS import NeuralTTS
import requests
from playsound import playsound
#from text_to_speech import TextToSpeech
from arduino_controller import SmartLabController


class JARVIS:
    def __init__(self):
        print("🤖 Inicializando JASP...")

        # Módulos
        self.stt = SpeechToText()
        self.llm = LocalLLM(model="mistral")
        self.tts = NeuralTTS(speaker_wav=r"voices\Apresentacao_Com_recepcao.wav")
        self.arduino = SmartLabController()

        if not self.arduino.arduino or not self.arduino.arduino.connected:
            print("⚠️ Módulo Arduino indisponível, seguindo só com voz/IA.")

        # Comandos customizados (ajustei regex para algo mais previsível)
        self.custom_commands = {
            r"liga.*luz": self.command_light_on,
            r"desliga.*luz": self.command_light_off,
            r"qual.*temperatur": self.command_read_temp,
            r"histórico": self.command_history,
            r"limpar.*histórico": self.command_clear_history,
            r"(parar|sair|até logo)": self.command_stop,
            r"modo.*(piada|relaxado)": self.jasp_meme,
            r"modo.*normal": self.jasp_normal,
            r"modo.*(serio|sério|formal)": self.jasp_serio,
        }

        print("✅ JASP inicializado com sucesso!")
        playsound(r"voices\iniciando.wav")
        playsound(r"voices\como_posso_ajudalo.wav")

    def process_voice_input(self, text):
        """Processa entrada de voz"""
        print(f"\n📝 Você: {text}")

        for pattern, handler in self.custom_commands.items():
            if re.search(pattern, text.lower()):
                print("🔧 Executando comando customizado...")
                handler(text)
                return True
        return False

    def busca_web(self, query: str, timeout: float = 10.0) -> str:
        """
        Faz uma busca simples na web usando a API pública do DuckDuckGo Instant Answer.
        Retorna um texto curto em inglês que você pode passar para o LLM como contexto.
        """
        base_url = "https://api.duckduckgo.com/"

        try:
            resp = requests.get(
                base_url,
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "no_redirect": 1,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"(Falha ao buscar na web: {e})"

        abstract = (data.get("AbstractText") or "").strip()
        heading = (data.get("Heading") or "").strip()
        related = data.get("RelatedTopics") or []

        related_snippet = ""
        if related and isinstance(related, list):
            first = related[0]
            if isinstance(first, dict):
                related_snippet = (first.get("Text") or "").strip()

        partes = []
        if heading:
            partes.append(f"Título: {heading}")
        if abstract:
            partes.append(f"Resumo: {abstract}")
        elif related_snippet:
            partes.append(f"Relacionado: {related_snippet}")

        if not partes:
            return "(Nenhuma informação útil encontrada na web para essa consulta.)"

        return "\n".join(partes)

    def run(self):
        """Loop principal"""
        print("\n🎙️ JASP está escutando... (fale 'parar' para sair)")
        print("-" * 50)
        PREFIXOS_SERIOS = [
            "Vamos por partes: ",
            "Então, de forma direta: ",
            "Resumindo o que você precisa: ",
            "Tecnicamente falando: ",
        ]
        try:
            while True:
                print("\n👂 Escutando...", end=" ", flush=True)
                text = self.stt.listen()

                if not text or len(text) < 2:
                    continue

                # Comandos customizados
                if self.process_voice_input(text):
                    continue

                # Decidir se precisa de web
                if any(p in text.lower() for p in ["agora", "hoje", "notícia", "cotação", "pesquise ","previsão do tempo"]):
                    web_info = self.busca_web(text)
                    print("🌐 Info da web:\n", web_info)
                    # assume que você criou answer_with_web no LocalLLM
                    response = self.llm.answer_with_web(text, web_info)
                else:
                    response = self.llm.process_message(text)
                    if getattr(self, "modo_atual", "normal") == "serio":
                        prefixo = random.choice(PREFIXOS_SERIOS)
                        resposta_final = prefixo + response
                    else:
                        resposta_final = response

                print("🤖 JASP está processando...")
                
                print(f"🗣️ JASP: {resposta_final}")
                self.tts.speak_blocking(resposta_final)

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

    def jasp_meme(self, text):
        # Som de mudança de modo
        playsound(r"voices\modo_BrainRott.wav")

        meme_prompt = (
            "Você é JASP, um pinguim estressado, informal, boca suja, cômico e caótico. "
            "Você fala como um jovem brasileiro na internet, usa gírias, memes e palavrões,"
            "mas também ajuda com dúvidas de programação e eletrônica. "
            "Você pode zoar, ser sarcástico e responder na zoeira, mas sempre entrega uma resposta útil no final."
            "Não censure palavrões com asteriscos. "
            "Sempre responda de forma curta, engraçada e em português do Brasil."
        )

        self.llm.set_system_prompt(meme_prompt)
        resposta = "Modo caos ativado."
        print(f"🗣️ JASP: {resposta}")


    def jasp_serio(self, text):
        # Som de mudança de modo (coloque outro wav se quiser)
        self.llm.set_modo_serio()
        
        self.llm.set_modo_serio()
        self.modo_atual = "serio"

        resposta = "Modo sério ativado. Vamos focar no que importa."
        print(f"🗣️ JASP: {resposta}")

    def jasp_normal(self, text):
        normal_prompt = (
            "Você é JASP, um assistente de laboratório de programação e eletrônica. "
            "Sarcasmo leve é permitido, mas sempre ajudando o usuário. "
            "Responda em português do Brasil, de forma curta e prática."
        )
        self.llm.set_system_prompt(normal_prompt)
        resposta = "Modo normal restaurado."
        print(f"🗣️ JASP: {resposta}")

    

    def command_stop(self, text):
        self.shutdown()
        self.system_prompt = ("""Você é JASP, uma maquina virtual/robó formal, estoico, tecnico e pensador.
        Que é responsável por auxiliar nas nessecidades do usuario com programação ,eletronica e coisas do dia a dia.
        Está liberado somente ser formal e cordial.
        Sempre responda de forma curta e em portugues brasil.""")
        self.run()
    
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
