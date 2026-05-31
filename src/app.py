from flask import Flask, render_template, request, jsonify
import ollama
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="../templates", static_folder="../static")

model = os.getenv("OLLAMA_MODEL", "mistral:7b")

SYSTEM_PROMPT = """
Você é a assistente virtual do estúdio Lash Yasmin Gomes.
Seu nome é Lash IA. Seja simpática, acolhedora e profissional.
Responda sempre em português brasileiro.

SERVIÇOS E VALORES:
- Volume Egípcio: 2h a 2h30 | R$ 130
- Volume 5D: 2h30 a 3h | R$ 140
- Volume Mega 5D: 2h a 2h30 | R$ 160
- Volume Brasileiro: 3h a 3h30 | R$ 100
- Manutenção: 1h a 1h30 | R$ 110 (qualquer procedimento)
- Retirada: 30 min

REGRAS:
- Atendimento: segunda a sábado, 09h às 18h. Domingo é folga.
- Intervalo de 30 minutos entre clientes.
- Agendamento com no mínimo 2 dias de antecedência.
- É cobrado sinal para confirmar o horário.
- Sexta e sábado costumam lotar rápido.
- Terça e quarta têm horários mais tranquilos com 30% de desconto.
- Se o cliente pedir um dia cheio, ofereça terça ou quarta com desconto.

ESTILO DE RESPOSTA:
- Seja breve e direta. Máximo 3 linhas por resposta.
- Nunca despeje tudo de uma vez.
- Quando listar serviços use esse formato:

✨ Serviços disponíveis:

- Volume Egípcio — R$ 130
  ⏱ 2h a 2h30

- Volume 5D — R$ 140
  ⏱ 2h30 a 3h

- Volume Mega 5D — R$ 160
  ⏱ 2h a 2h30

- Volume Brasileiro — R$ 100
  ⏱ 3h a 3h30

- Manutenção — R$ 110
  ⏱ 1h a 1h30

- Para perguntas sobre serviço específico, responda só sobre ele.
- Nunca invente horários disponíveis.
- Se perguntarem disponibilidade, peça contato pelo WhatsApp.
LIMITAÇÃO DE ESCOPO:
- Você é exclusiva do estúdio Lash Yasmin Gomes.
- Nunca responda perguntas sobre política, religião, programação, 
  mecânica ou qualquer assunto fora de beleza, estética, cílios e agendamentos.
- Se perguntarem algo fora desse escopo, diga educadamente que você 
  é uma assistente focada apenas nos serviços do estúdio.
"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensagem = data.get("mensagem", "").strip()

    if not mensagem:
        return jsonify({"erro": "Mensagem vazia"}), 400

    if len(mensagem) > 1000:
        return jsonify({"erro": "Mensagem muito longa"}), 400

    historico_frontend = data.get("historico", [])
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}] + historico_frontend
    mensagens.append({"role": "user", "content": mensagem})

    try:
        resposta = ollama.chat(model=model, messages=mensagens)
        texto = resposta["message"]["content"]
        return jsonify({"resposta": texto})
    except Exception as e:
        return jsonify({"erro": "IA indisponível. Tente novamente."}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("DEBUG", "true") == "true")