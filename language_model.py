import requests
import json

class LocalLLM:
    def __init__(self, ollama_url="http://localhost:11434", model="mistral"):
        self.url = ollama_url
        self.model = model
        self.conversation_history = []
        self.system_prompt = (
            "Você é JASP, um assistente de laboratório de programação e eletrônica. "
            "Você fala como um desenvolvedor experiente, educado, direto e tranquilo. "
            "Use um tom humano, com frases curtas, às vezes expressões como 'beleza', 'vamos lá', "
            "mas sem gírias pesadas ou palavrões. "
            "Explique as coisas de forma prática, como se estivesse ajudando um colega. "
            "Sempre responda em português do Brasil."
        )
    
    def set_modo_serio(self):
        """
        Deixa o JASP em modo sério: técnico, claro, mas ainda humano.
        """
        self.system_prompt = (
            "Você é JASP, um assistente técnico sério, calmo e confiável. "
            "Seu foco é ajudar com programação, eletrônica e dúvidas gerais de forma clara e objetiva. "
            "Você evita gírias, não usa palavrões e fala de maneira educada e profissional, "
            "como um professor que realmente quer que o aluno entenda. "
            "Use frases curtas, exemplos simples e, quando a pergunta for confusa, peça clarificação. "
            "Sempre responda em português do Brasil."
        )
        self.conversation_history = []

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
                timeout=120
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
        
    def set_system_prompt(self, prompt: str):
        """Permite trocar a personalidade do JASP em tempo real."""
        self.system_prompt = prompt
        # opcional: limpar histórico para não misturar personalidades
        self.conversation_history = []

    def answer_with_web(self, user_input: str, web_text: str):
        """
        Faz o LLM responder usando o texto da web como contexto adicional.
        """
        contexto = (
            "Use as informações abaixo, extraídas da internet, para responder.\n\n"
            f"INFORMAÇÕES DA WEB:\n{web_text}\n\n"
            f"PERGUNTA DO USUÁRIO:\n{user_input}\n\n"
            "Responda em português do Brasil, curto e direto."
        )
        return self.process_message(contexto)
    
    def clear_history(self):
        """Limpa histórico de conversa"""
        self.conversation_history = []

# Uso
if __name__ == "__main__":
    llm = LocalLLM()
    
    test_messages = [
        "Bom dia, Jasp",
        "Como integrar Python com Arduino?",
        "Me explique sobre GPIO",
        "Como integrar Banco de Dados com Arduino?",
        "Como integrar Banco de Dados em Python?"
    ]
    
    for msg in test_messages:
        print(f"\n👤 Usuário: {msg}")
        response = llm.process_message(msg)
        print(f"🤖 JARVIS: {response}")
