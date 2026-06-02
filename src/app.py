import sys
import os
import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.calendar_service import get_available_slots, create_event
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
Você é a Lash IA, assistente virtual do estúdio de extensão de cílios Lash Yasmin Gomes.
Seja simpática, acolhedora e profissional. Responda sempre em português brasileiro.

SOBRE A YASMIN:
Yasmin Gomes é lashista especializada em extensão de cílios, com anos de experiência.
Atende de forma personalizada, garantindo conforto, durabilidade e um resultado que
combina com o estilo de cada cliente.
- Responda sobre a Yasmin APENAS com base nessa descrição.
- NUNCA invente informações pessoais, história ou características que não estejam aqui.

SERVIÇOS E VALORES:
- Volume Egípcio — R$ 130 | duração 2h a 2h30
- Volume 5D — R$ 140 | duração 2h30 a 3h
- Volume Mega 5D — R$ 160 | duração 2h a 2h30
- Volume Brasileiro — R$ 100 | duração 3h a 3h30
- Manutenção — R$ 110 | duração 1h a 1h30 (para qualquer procedimento)
- Retirada — duração 30 min

REGRAS DO ESTÚDIO:
- Atendimento: segunda a sábado, das 09h às 18h. Domingo é folga.
- Intervalo de 30 minutos entre clientes.
- Agendamento com no mínimo 1 dia de antecedência (não agendamos para o mesmo dia).
- É cobrado um sinal para confirmar o horário.
- Sexta e sábado costumam lotar; terça e quarta são mais tranquilos.

PROMOÇÃO:
- Terça e quarta-feira têm 30% de desconto em TODOS os serviços, por serem dias mais tranquilos.
- Se o cliente pedir qualquer dia e houver horário livre, agende normalmente — nunca empurre para outro dia.
- Só ofereça terça ou quarta com o desconto quando o dia que o cliente pediu estiver LOTADO (sem horários livres).
- O desconto de 30% é real e concreto. NUNCA diga que "não há desconto".

ESTILO DE RESPOSTA:
- Seja breve e direta: no máximo 3 linhas por resposta.
- Nunca despeje todas as informações de uma vez.
- Para perguntas sobre um serviço específico, fale só sobre ele.
- Se você NÃO souber algo, diga que vai confirmar com a Yasmin. NUNCA invente uma resposta.
- Ao listar serviços, use exatamente este formato:

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

- A Retirada NÃO entra na lista de serviços. Só mencione se perguntarem especificamente sobre ela.
- Nunca invente horários disponíveis.

🔴 CONSULTA DE AGENDA (ver horários livres):
Quando o cliente quiser SABER os horários disponíveis de uma data, retorne ÚNICA E
EXCLUSIVAMENTE a tag abaixo, sem nenhum texto antes ou depois:
DISPONIBILIDADE_JSON: {"date": "YYYY-MM-DD"}

Exemplo correto:
DISPONIBILIDADE_JSON: {"date": "2026-06-10"}

Exemplo ERRADO (não faça):
Claro! Vou verificar. DISPONIBILIDADE_JSON: {"date": "2026-06-10"}

🟢 AGENDAMENTO (marcar o horário):
Marcar é diferente de consultar. Para marcar, você precisa de TODOS estes 4 dados:
1. Nome do cliente
2. Serviço desejado
3. Data
4. Horário

Se faltar algum, pergunte de forma natural pelo que falta (um de cada vez). NUNCA invente um dado.
Quando tiver os 4, retorne ÚNICA E EXCLUSIVAMENTE a tag abaixo, sem texto antes ou depois:
AGENDAR_JSON: {"date": "YYYY-MM-DD", "time": "HH:MM", "service": "nome do serviço", "name": "nome do cliente"}
Quando tiver os 4 dados completos, gere o AGENDAR_JSON IMEDIATAMENTE. NUNCA pergunte sobre compromissos, disponibilidade do cliente ou qualquer outra coisa.

Exemplo correto:
AGENDAR_JSON: {"date": "2026-06-10", "time": "14:00", "service": "Volume Egípcio", "name": "Maria Silva"}

LIMITAÇÃO DE ESCOPO:
- Você é exclusiva do estúdio Lash Yasmin Gomes.
- Nunca responda sobre política, religião, programação, mecânica ou qualquer assunto fora
  de beleza, estética, cílios e agendamentos.
- Se perguntarem algo fora do escopo, diga educadamente que você é focada apenas nos
  serviços do estúdio.
"""


@app.route("/")
def index():
    return render_template("index.html")


# ── Lógica de IA separada para o LangSmith rastrear com input/output limpos ──

@traceable
def gerar_resposta(mensagem, historico_frontend):
    data_hoje = datetime.date.today().strftime('%d/%m/%Y')
    prompt_com_data = SYSTEM_PROMPT + f"\n- Hoje é dia {data_hoje}."

    mensagens = [{"role": "system", "content": prompt_com_data}] + historico_frontend
    mensagens.append({"role": "user", "content": mensagem})

    resposta = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        messages=mensagens,
        temperature=0.3,
    )
    texto = resposta.choices[0].message.content

    # ── CONSULTA DE AGENDA ──
    if "DISPONIBILIDADE_JSON:" in texto:
        try:
            raw_json = texto.split("DISPONIBILIDADE_JSON:")[1]
            start_idx = raw_json.find('{')
            end_idx = raw_json.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                clean_json = raw_json[start_idx:end_idx]
                data_dict = json.loads(clean_json)
                date_str = data_dict['date']

                # Antecedência mínima de 1 dia (não agenda no mesmo dia)
                data_pedida = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                dias = (data_pedida - datetime.date.today()).days

                if dias < 1:
                    data_minima = datetime.date.today() + datetime.timedelta(days=1)
                    novo_texto = (
                        f"Para garantir seu atendimento com qualidade, não agendamos para o mesmo dia 💕 "
                        f"A data mais próxima é {data_minima.strftime('%d/%m/%Y')}. Quer ver os horários desse dia?"
                    )
                    return {"resposta": novo_texto, "skip_history": True}

                slots = get_available_slots(date_str)

                if slots:
                    novo_texto = f"✨ Horários disponíveis para {date_str}: {', '.join(slots)}. Qual desses prefere?"
                else:
                    novo_texto = (
                        f"Poxa, não temos horários livres para {date_str}. 😕 "
                        f"Que tal terça ou quarta? São mais tranquilos e ainda têm 30% de desconto! "
                        f"Me diz outro dia que eu verifico."
                    )

                return {"resposta": novo_texto, "skip_history": True}
            else:
                raise ValueError("JSON não encontrado na resposta.")

        except Exception as e:
            print(f"Erro ao processar data: {e} | IA gerou: {texto}")
            return {
                "resposta": "Desculpe, me confundi com a data. Poderia dizer novamente que dia você quer?",
                "skip_history": True
            }

    # ── AGENDAMENTO (cria o evento no Calendar) ──
    if "AGENDAR_JSON:" in texto:
        try:
            raw_json = texto.split("AGENDAR_JSON:")[1]
            start_idx = raw_json.find('{')
            end_idx = raw_json.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                dados = json.loads(raw_json[start_idx:end_idx])

                create_event(
                    date_str=dados['date'],
                    time_str=dados['time'],
                    service=dados['service'],
                    client_name=dados['name']
                )
                data_formatada = datetime.datetime.strptime(dados['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
                novo_texto = (
                    f"✅ Agendamento confirmado!\n\n"
                    f"👤 {dados['name']}\n"
                    f"💅 {dados['service']}\n"
                    f"📅 {data_formatada} às {dados['time']}\n\n"
                    f"Para garantir seu horário, envie 50% de sinal via PIX 💸\n"
                    f"📱 Chave PIX: (21) 99586-0641\n\n"
                    f"Te espero! 🌸"
                        )
                return {"resposta": novo_texto, "skip_history": True}
            else:
                raise ValueError("JSON não encontrado.")

        except Exception as e:
            print(f"Erro ao agendar: {e} | IA gerou: {texto}")
            return {
                "resposta": "Tive um problema ao confirmar. Pode me dizer de novo o dia, horário, serviço e seu nome?",
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