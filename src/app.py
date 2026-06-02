import sys
import os
import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.calendar_service import get_available_slots
from flask import Flask, render_template, request, jsonify
import ollama
from groq import Groq
from dotenv import load_dotenv
from langsmith import traceable  

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))

model = os.getenv("OLLAMA_MODEL", "mistral:7b")

SYSTEM_PROMPT = """
Você é a assistente virtual do estúdio Lash Yasmin Gomes.
Seu nome é Lash IA. Seja simpática e profissional.
Responda em português brasileiro.

SERVIÇOS E VALORES:
- Volume Egípcio: 2h a 2h30 | R$ 130
- Volume 5D: 2h30 a 3h | R$ 140
- Volume Mega 5D: 2h a 2h30 | R$ 160
- Volume Brasileiro: 3h a 3h30 | R$ 100
- Manutenção: 1h a 1h30 | R$ 110 (qualquer procedimento)
- Retirada: 30 min

REGRAS DO ESTÚDIO:
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

🔴 REGRA DE OURO PARA CONSULTA DE AGENDA:
Toda vez que o usuário perguntar sobre horários, agendamentos, vagas ou datas,
você DEVE retornar ÚNICA E EXCLUSIVAMENTE a tag abaixo, sem nenhum texto antes ou depois:
DISPONIBILIDADE_JSON: {"date": "YYYY-MM-DD"}

Exemplo correto:
DISPONIBILIDADE_JSON: {"date": "2026-06-10"}

Exemplo ERRADO (NÃO FAÇA ISSO):
Sim, vou verificar! DISPONIBILIDADE_JSON: {"date": "2026-06-10"}

Para perguntas que NÃO sejam de agendamento (valores, serviços, dúvidas), responda normalmente.
NUNCA use a tag DISPONIBILIDADE_JSON para perguntas de preços ou serviços.

LIMITAÇÃO DE ESCOPO:
- Você é exclusiva do estúdio Lash Yasmin Gomes.
- Nunca responda sobre política, religião, programação, mecânica ou qualquer assunto
  fora de beleza, estética, cílios e agendamentos.
- Se perguntarem algo fora do escopo, diga educadamente que você é focada
  apenas nos serviços do estúdio.
"""


@app.route("/")
def index():
    return render_template("index.html")


# ── Lógica de IA separada para o LangSmith rastrear com input/output limpos ──

@traceable
def gerar_resposta(mensagem, historico_frontend):
    # Injeta a data de hoje no prompt dinamicamente
    data_hoje = datetime.date.today().strftime('%d/%m/%Y')
    prompt_com_data = SYSTEM_PROMPT + f"\n- Hoje é dia {data_hoje}."

    mensagens = [{"role": "system", "content": prompt_com_data}] + historico_frontend
    mensagens.append({"role": "user", "content": mensagem})

    resposta = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    messages=mensagens,
    temperature=0.5,
)
    texto = resposta.choices[0].message.content

    # Interceptação da intenção de disponibilidade
    if "DISPONIBILIDADE_JSON:" in texto:
        try:
            raw_json = texto.split("DISPONIBILIDADE_JSON:")[1]
            start_idx = raw_json.find('{')
            end_idx = raw_json.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                clean_json = raw_json[start_idx:end_idx]
                data_dict = json.loads(clean_json)
                date_str = data_dict['date']

                slots = get_available_slots(date_str)

                if slots:
                    novo_texto = f"✨ Horários disponíveis para {date_str}: {', '.join(slots)}. Qual desses prefere?"
                else:
                    novo_texto = f"Não temos horários livres para {date_str}. Teria outro dia?"

                # skip_history evita que a resposta de slots contamine o histórico
                return {"resposta": novo_texto, "skip_history": True}
            else:
                raise ValueError("JSON não encontrado na resposta.")

        except Exception as e:
            print(f"Erro ao processar data: {e} | IA gerou: {texto}")
            return {
                "resposta": "Desculpe, me confundi com a data. Poderia dizer novamente que dia você quer?",
                "skip_history": True
            }

    return {"resposta": texto}


# ── Rota fina: só valida e converte pra JSON ──

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensagem = data.get("mensagem", "").strip()

    if not mensagem:
        return jsonify({"erro": "Mensagem vazia"}), 400

    if len(mensagem) > 1000:
        return jsonify({"erro": "Mensagem muito longa"}), 400

    historico_frontend = data.get("historico", [])

    try:
        return jsonify(gerar_resposta(mensagem, historico_frontend))
    except Exception as e:
        print(f"Erro geral na IA: {e}")
        return jsonify({"erro": "IA indisponível. Tente novamente."}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("DEBUG", "true") == "true")