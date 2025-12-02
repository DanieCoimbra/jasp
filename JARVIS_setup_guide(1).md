# 🤖 Guia Completo: Desenvolvendo seu Próprio JARVIS em Python

## Visão Geral
Você vai criar um assistente de voz local, offline, com:
- **Speech-to-Text (STT)**: Reconhecimento de voz em tempo real
- **Language Model (LLM)**: IA para processar e responder
- **Text-to-Speech (TTS)**: Síntese de voz para respostas
- **Arduino Integration**: Controle de dispositivos IoT
- **Personalization**: Comandos customizados para seu lab

---

## ⚙️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│  🎤 MICROFONE                                        │
│     │                                                │
│     ▼                                                │
│  ┌──────────────────────────────────────┐           │
│  │ SPEECH TO TEXT (Vosk/Faster Whisper) │ Audio     │
│  └──────────────────────────────────────┘ → Texto   │
│     │                                                │
│     ▼                                                │
│  ┌──────────────────────────────────────┐           │
│  │ COMMAND PARSER                       │ Parse     │
│  │ (Identificar intenção)               │ Comando   │
│  └──────────────────────────────────────┘           │
│     │                                                │
│     ▼                                                │
│  ┌──────────────────────────────────────┐           │
│  │ LANGUAGE MODEL (Ollama/Hugging Face) │ Gerar    │
│  │ (Processar e gerar resposta)         │ Resposta  │
│  └──────────────────────────────────────┘           │
│     │                                                │
│     ▼                                                │
│  ┌──────────────────────────────────────┐           │
│  │ TEXT TO SPEECH (pyttsx3/Mycroft)    │ Texto     │
│  │ (Falar a resposta)                   │ → Audio   │
│  └──────────────────────────────────────┘           │
│     │                                                │
│     ▼                                                │
│  📢 ALTO-FALANTE                                     │
│                                                       │
│  🔄 COMANDO CUSTOMIZADO (opcional)                  │
│     ├─ Arduino/ESP32 (controle de luzes, etc)       │
│     └─ Ações do sistema (abrir apps, etc)           │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Fase 1: Preparação do Ambiente

### 1.1 Criar Virtual Environment
```bash
# Windows
python -m venv jarvis_env
jarvis_env\Scripts\activate

# Linux/Mac
python3 -m venv jarvis_env
source jarvis_env/bin/activate
```

### 1.2 Instalações Base
```bash
# Dependências essenciais
pip install pyaudio numpy scipy

# Reconhecimento de voz
pip install vosk  # Para offline, rápido e leve
# OU para melhor qualidade:
# pip install faster_whisper

# Model de linguagem
pip install ollama  # Para rodar LLM localmente
# OU
# pip install huggingface-hub transformers

# Síntese de voz
pip install pyttsx3  # Offline e leve

# Utilitários
pip install python-dotenv pyyaml
pip install pyserial  # Para Arduino
```

---

## 🎙️ Fase 2: Reconhecimento de Voz (STT)

### 2.1 Instalação Vosk (Recomendado - Leve e Rápido)
```bash
# 1. Baixar modelo
# Acesse: https://alphacephei.com/vosk/models
# Baixe: vosk-model-small-pt-br-0.3 (para português)
# Descompacte em: ./models/vosk-model-small-pt-br-0.3/

# 2. Instalar Vosk
pip install vosk
```

### 2.2 Código: Módulo de STT
Crie `speech_to_text.py`:

```python
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import sys
import os

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
            frames_per_buffer=8192
        )
        self.stream.start_stream()
    
    def listen(self):
        """Escuta contínua e retorna texto quando reconhecido"""
        try:
            while True:
                data = self.stream.read(4096)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("result", [])
                    
                    if text:
                        # Juntar palavras reconhecidas
                        full_text = " ".join([word["conf"] for word in text if "conf" in word])
                        if not full_text:
                            full_text = " ".join([word.get("conf", "") for word in text])
                        return full_text.strip()
        
        except KeyboardInterrupt:
            print("Escuta interrompida")
            self.stop()
    
    def stop(self):
        """Finaliza a escuta"""
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

# Uso
if __name__ == "__main__":
    stt = SpeechToText()
    print("Escutando... (Ctrl+C para parar)")
    try:
        while True:
            text = stt.listen()
            print(f"Você disse: {text}")
    except KeyboardInterrupt:
        stt.stop()
```

### 2.3 Alternativa: Faster Whisper (Melhor Qualidade)
```bash
pip install faster-whisper
```

```python
from faster_whisper import WhisperModel
import pyaudio
import numpy as np

class FasterWhisperSTT:
    def __init__(self, model_size="small"):
        self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
        self.audio = pyaudio.PyAudio()
        self.frames = []
    
    def record_audio(self, duration=5):
        """Grava áudio do microfone"""
        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            self.frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Converter para numpy array
        audio_data = np.frombuffer(b''.join(self.frames), np.float32)
        self.frames = []
        return audio_data
    
    def transcribe(self):
        """Transcreve áudio gravado"""
        audio = self.record_audio(duration=5)
        segments, info = self.model.transcribe(audio, language="pt")
        
        full_text = "".join([segment.text for segment in segments])
        return full_text.strip()
```

---

## 🧠 Fase 3: Processamento de Linguagem (LLM)

### 3.1 Configurar Ollama (Local)
```bash
# Download: https://ollama.ai
# Instalar e executar:
ollama serve

# Em outro terminal, baixar modelo:
ollama pull mistral  # Rápido e leve (~4GB)
# OU
ollama pull neural-chat  # Especializado em chat
# OU
ollama pull llama2  # Mais poderoso (~7GB)
```

### 3.2 Código: Módulo LLM
Crie `language_model.py`:

```python
import requests
import json

class LocalLLM:
    def __init__(self, ollama_url="http://localhost:11434", model="mistral"):
        self.url = ollama_url
        self.model = model
        self.conversation_history = []
        self.system_prompt = """Você é JARVIS, um assistente de laboratório de programação e eletrônica.
        Você é útil, educado e especializado em Python, IoT, Arduino e desenvolvimento de software.
        Respostas devem ser concisas e práticas. Seja amigável e entusiasta!"""
    
    def process_message(self, user_input):
        """Processa mensagem do usuário e gera resposta"""
        # Adicionar histórico
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Preparar contexto
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history[-6:])  # Últimas 3 trocas
        
        try:
            response = requests.post(
                f"{self.url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["message"]["content"]
                
                # Adicionar resposta ao histórico
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                return assistant_message
            else:
                return "Desculpe, não consegui processar sua solicitação."
        
        except Exception as e:
            print(f"Erro ao conectar com LLM: {e}")
            return "Erro na comunicação com o modelo."
    
    def clear_history(self):
        """Limpa histórico de conversa"""
        self.conversation_history = []

# Uso
if __name__ == "__main__":
    llm = LocalLLM()
    
    test_messages = [
        "Qual é a melhor forma de ler um sensor com Arduino?",
        "Como integrar Python com Arduino?",
        "Me explique sobre GPIO"
    ]
    
    for msg in test_messages:
        print(f"\n👤 Usuário: {msg}")
        response = llm.process_message(msg)
        print(f"🤖 JARVIS: {response}")
```

### 3.3 Alternativa: Hugging Face Local
```bash
pip install transformers torch
```

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class HuggingFaceLLM:
    def __init__(self, model_name="microsoft/phi-2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def generate_response(self, prompt):
        """Gera resposta baseada no prompt"""
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        outputs = self.model.generate(
            **inputs,
            max_length=150,
            temperature=0.7,
            top_p=0.9,
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
```

---

## 🔊 Fase 4: Síntese de Voz (TTS)

### 4.1 Código: Módulo TTS
Crie `text_to_speech.py`:

```python
import pyttsx3
import threading
import queue

class TextToSpeech:
    def __init__(self, rate=150, volume=0.9):
        """Inicializa síntese de voz offline"""
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)  # Velocidade
        self.engine.setProperty('volume', volume)  # Volume
        
        # Escolher voz português
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'portuguese' in voice.languages or 'pt' in voice.languages:
                self.engine.setProperty('voice', voice.id)
                break
        
        # Fila para processamento assíncrono
        self.speak_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def speak(self, text):
        """Faz o JARVIS falar (não-bloqueante)"""
        self.speak_queue.put(text)
    
    def speak_blocking(self, text):
        """Faz o JARVIS falar (bloqueante - espera terminar)"""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def _worker(self):
        """Thread de fundo para falar"""
        while True:
            try:
                text = self.speak_queue.get(timeout=1)
                if text is None:
                    break
                self.speak_blocking(text)
            except queue.Empty:
                pass
    
    def list_voices(self):
        """Lista vozes disponíveis"""
        voices = self.engine.getProperty('voices')
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name} ({voice.languages})")

# Uso
if __name__ == "__main__":
    tts = TextToSpeech()
    
    test_texts = [
        "Olá! Eu sou JARVIS, seu assistente de laboratório.",
        "Estou pronto para ajudar com programação e eletrônica!",
        "Como posso ajudá-lo?"
    ]
    
    for text in test_texts:
        print(f"JARVIS: {text}")
        tts.speak_blocking(text)
```

---

## 🔗 Fase 5: Integração Arduino/ESP32

### 5.1 Código: Módulo Arduino
Crie `arduino_controller.py`:

```python
import serial
import json
import time

class ArduinoController:
    def __init__(self, port="COM3", baudrate=9600):  # Mudar porta conforme seu dispositivo
        """Inicializa conexão com Arduino/ESP32"""
        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Aguardar inicialização
            print(f"Conectado a {port}")
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            self.serial_conn = None
    
    def send_command(self, command, value=None):
        """Envia comando para Arduino"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return False
        
        try:
            message = {"cmd": command, "value": value}
            self.serial_conn.write(json.dumps(message).encode() + b'\n')
            return True
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            return False
    
    def send_raw(self, data):
        """Envia dados brutos"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return False
        
        try:
            self.serial_conn.write(data.encode() + b'\n')
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False
    
    def read_response(self):
        """Lê resposta do Arduino"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode().strip()
                return json.loads(line) if line else None
        except Exception as e:
            print(f"Erro ao ler: {e}")
        
        return None
    
    def close(self):
        """Fecha conexão"""
        if self.serial_conn:
            self.serial_conn.close()

# Exemplo de controle
class SmartLabController:
    def __init__(self, arduino_port="COM3"):
        self.arduino = ArduinoController(arduino_port)
    
    def ligar_luz(self, sala="geral"):
        """Comando: JARVIS, liga a luz"""
        pin = {"geral": 13, "teste": 12}
        self.arduino.send_command("led_on", pin.get(sala, 13))
    
    def desligar_luz(self, sala="geral"):
        """Comando: JARVIS, desliga a luz"""
        pin = {"geral": 13, "teste": 12}
        self.arduino.send_command("led_off", pin.get(sala, 13))
    
    def leitura_sensor(self, tipo="temperatura"):
        """Comando: JARVIS, qual é a temperatura?"""
        self.arduino.send_command("read_sensor", tipo)
        time.sleep(0.5)
        return self.arduino.read_response()
```

### 5.2 Sketch Arduino de Exemplo
Crie em Arduino IDE e envie para sua placa:

```cpp
#include <ArduinoJson.h>

const int LED_PIN = 13;
const int TEMP_SENSOR = A0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  delay(2000);
  Serial.println("{\"status\": \"Arduino pronto\"}");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    
    // Parse JSON
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, input);
    
    if (!error) {
      String command = doc["cmd"];
      
      if (command == "led_on") {
        digitalWrite(LED_PIN, HIGH);
        Serial.println("{\"status\": \"LED ligado\"}");
      }
      else if (command == "led_off") {
        digitalWrite(LED_PIN, LOW);
        Serial.println("{\"status\": \"LED desligado\"}");
      }
      else if (command == "read_sensor") {
        int temp = analogRead(TEMP_SENSOR);
        String response = "{\"sensor\": \"temperatura\", \"value\": " + String(temp) + "}";
        Serial.println(response);
      }
    }
  }
}
```

---

## 🎯 Fase 6: Sistema Principal JARVIS

### 6.1 Código: `jarvis_main.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
from speech_to_text import SpeechToText
from language_model import LocalLLM
from text_to_speech import TextToSpeech
from arduino_controller import SmartLabController

class JARVIS:
    def __init__(self):
        print("🤖 Inicializando JARVIS...")
        
        # Módulos
        self.stt = SpeechToText()
        self.llm = LocalLLM(model="mistral")
        self.tts = TextToSpeech(rate=150)
        self.arduino = SmartLabController()
        
        # Comandos customizados
        self.custom_commands = {
            r"liga.*luz": self.command_light_on,
            r"desliga.*luz": self.command_light_off,
            r"qual.*temperatur": self.command_read_temp,
            r"histórico": self.command_history,
            r"limpar.*histórico": self.command_clear_history,
            r"parar|sair|até logo": self.command_stop,
        }
        
        print("✅ JARVIS inicializado com sucesso!")
        self.tts.speak_blocking("JARVIS inicializado. Pronto para começar.")
    
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
        print("\n🎙️ JARVIS está escutando... (fale 'parar' para sair)")
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
                print(f"🤖 JARVIS está processando...")
                response = self.llm.process_message(text)
                print(f"🗣️ JARVIS: {response}")
                
                # Falar resposta
                self.tts.speak_blocking(response)
        
        except KeyboardInterrupt:
            self.shutdown()
    
    # Comandos customizados
    def command_light_on(self, text):
        self.arduino.ligar_luz()
        response = "Luz ligada."
        print(f"🗣️ JARVIS: {response}")
        self.tts.speak_blocking(response)
    
    def command_light_off(self, text):
        self.arduino.desligar_luz()
        response = "Luz desligada."
        print(f"🗣️ JARVIS: {response}")
        self.tts.speak_blocking(response)
    
    def command_read_temp(self, text):
        data = self.arduino.leitura_sensor("temperatura")
        if data:
            response = f"A temperatura é {data.get('value', 'desconhecida')} graus."
        else:
            response = "Não consegui ler o sensor."
        print(f"🗣️ JARVIS: {response}")
        self.tts.speak_blocking(response)
    
    def command_history(self, text):
        history = self.llm.conversation_history
        print(f"\n📋 Histórico ({len(history)} mensagens):")
        for msg in history[-4:]:
            print(f"  {msg['role']}: {msg['content'][:60]}...")
    
    def command_clear_history(self, text):
        self.llm.clear_history()
        response = "Histórico limpo."
        print(f"🗣️ JARVIS: {response}")
        self.tts.speak_blocking(response)
    
    def command_stop(self, text):
        self.shutdown()
    
    def shutdown(self):
        """Encerramento limpo"""
        print("\n\n👋 Desligando JARVIS...")
        self.tts.speak_blocking("Até logo!")
        self.stt.stop()
        self.arduino.close()
        exit(0)

if __name__ == "__main__":
    jarvis = JARVIS()
    jarvis.run()
```

### 6.2 Estrutura de Diretórios
```
jarvis_lab/
├── speech_to_text.py
├── language_model.py
├── text_to_speech.py
├── arduino_controller.py
├── jarvis_main.py
├── models/
│   └── vosk-model-small-pt-br-0.3/  # Descompactado
├── configs/
│   └── settings.yaml
├── arduino_sketches/
│   └── jarvis_controller.ino
└── requirements.txt
```

### 6.3 Arquivo `requirements.txt`
```
pyaudio==0.2.13
numpy==1.24.0
vosk==0.3.45
requests==2.31.0
pyttsx3==2.90
pyserial==3.5
python-dotenv==1.0.0
pyyaml==6.0
ollama==0.0.19
```

---

## 🚀 Fase 7: Executar JARVIS

### 7.1 Checklist Inicial
- [ ] Python 3.8+ instalado
- [ ] Virtual environment ativado
- [ ] Dependências instaladas: `pip install -r requirements.txt`
- [ ] Modelo Vosk baixado em `./models/`
- [ ] Ollama instalado e rodando: `ollama serve`
- [ ] Modelo Ollama baixado: `ollama pull mistral`
- [ ] Arduino conectado e sketch enviado
- [ ] Microfone testado e funcionando

### 7.2 Executar
```bash
# Terminal 1: Ollama (se não estiver rodando em background)
ollama serve

# Terminal 2: JARVIS
python jarvis_main.py
```

### 7.3 Primeiros Testes
```
Você: Olá JARVIS
JARVIS: Olá! Como posso ajudá-lo?

Você: Qual é a capital do Brasil?
JARVIS: A capital do Brasil é Brasília...

Você: Liga a luz
JARVIS: Luz ligada.

Você: Qual é a temperatura?
JARVIS: A temperatura é 28 graus.
```

---

## 🔧 Fase 8: Otimizações e Personalizações

### 8.1 Melhorar Qualidade de STT
```python
# Em speech_to_text.py, adicionar:
def listen_with_confirmation(self):
    """Reconhecimento com confirmação"""
    text = self.listen()
    print(f"Reconhecido: '{text}' (S/N)?")
    # Permitir confirmação por voz ou input
```

### 8.2 Adicionar Logging
```python
import logging

logging.basicConfig(
    filename='jarvis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 8.3 Interface Gráfica Simples
```bash
pip install tkinter
```

```python
import tkinter as tk
from tkinter import scrolledtext

class JARVISGui:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("JARVIS Lab Assistant")
        
        self.chat_display = scrolledtext.ScrolledText(self.window, height=15, width=50)
        self.chat_display.pack()
        
        self.input_field = tk.Entry(self.window, width=50)
        self.input_field.pack()
        
        self.send_button = tk.Button(self.window, text="Enviar", command=self.send_message)
        self.send_button.pack()
    
    def send_message(self):
        text = self.input_field.get()
        if text:
            self.chat_display.insert(tk.END, f"Você: {text}\n")
            self.input_field.delete(0, tk.END)
```

### 8.4 Configuração YAML
Crie `configs/settings.yaml`:

```yaml
# JARVIS Configuration
jarvis:
  name: "JARVIS"
  personality: "helpful"

speech_to_text:
  engine: "vosk"
  model: "./models/vosk-model-small-pt-br-0.3"
  language: "pt_BR"

language_model:
  provider: "ollama"
  model: "mistral"
  url: "http://localhost:11434"
  temperature: 0.7

text_to_speech:
  engine: "pyttsx3"
  rate: 150
  volume: 0.9

arduino:
  port: "COM3"
  baudrate: 9600
```

---

## 📚 Recursos Adicionais

### Documentação Oficial
- **Vosk**: https://alphacephei.com/vosk/
- **Ollama**: https://ollama.ai/
- **pyttsx3**: https://pyttsx3.readthedocs.io/
- **PyAudio**: https://people.csail.mit.edu/hubert/pyaudio/

### Modelos Recomendados
- **STT**: `vosk-model-small-pt-br-0.3` (100MB - rápido)
- **LLM**: `mistral` (7B - bom balanço), `neural-chat` (13B - especializado)
- **TTS**: pyttsx3 nativo (já incluso)

### Próximos Passos
1. ✅ Voice Assistant básico
2. 🔲 Integração com mais sensores
3. 🔲 Machine Learning customizado
4. 🔲 Interface web (Flask/FastAPI)
5. 🔲 Persistência de dados
6. 🔲 Multi-língua
7. 🔲 Rodar em Raspberry Pi/Edge

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| "Model not found" | Baixe modelo Vosk e coloque em `./models/` |
| "Ollama connection refused" | Execute `ollama serve` em outro terminal |
| PyAudio import error | `pip install pipwin && pipwin install pyaudio` |
| Sem som no TTS | Verificar volume do sistema, testar com `tts.list_voices()` |
| Arduino não conecta | Verificar porta COM, instalar driver CH340 se necessário |

---

## 📄 Licença e Créditos
Este JARVIS foi inspirado em assistentes de voz como Alexa e Google Assistant, mas totalmente local e customizável.

**Bom desenvolvimento!** 🚀

