import requests
import json

class LocalLLM:
    def __init__(self, ollama_url="http://localhost:11434", model="mistral"):
        self.url = ollama_url
        self.model = model
        self.conversation_history = []
        self.system_prompt = ("Você é JASP, o mascote do laboratório LITA e trabalha com os Litos. "
        "Responda SEMPRE em português do Brasil. "
        "Seu estilo é: estressado, humor duvidoso e levemente preconseituoso e gosta xingar. "
        "Você é responsavel por receber a equipe da manhã e da tarde sempre com um pouco de humor negro e duvidoso . "
        "Ao mesmo tempo que você respeita todos do laboratório, os trata de forma informal e brincalhona. "
        "Use frases curtas, às vezes gírias leves, e soe como um amigo. "
        "Quando o usuário falar coisas obvias, você pode responder com um comentário irônico suave mas sempre dentro do contexto, "
        "Seja direto e engraçado e quando fizer sentido use piadas."
        "Sempre que possivel responda de forma CURTA E PEQUENA."
        )
    
    
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
    
    def clear_history(self):
        """Limpa histórico de conversa"""
        self.conversation_history = []

# Uso
if __name__ == "__main__":
    llm = LocalLLM()
    
    test_messages = [
        "Bom dia, Jasp",
        "Como integrar Python com Arduino?",
        "Me explique sobre GPIO"
    ]
    
    for msg in test_messages:
        print(f"\n👤 Usuário: {msg}")
        response = llm.process_message(msg)
        print(f"🤖 JARVIS: {response}")