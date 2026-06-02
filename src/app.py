from langsmith import traceable
from dotenv import load_dotenv
from groq import Groq
import ollama
from flask import Flask, render_template, request, jsonify
from services.calendar_service import get_available_slots, create_event
import sys
import os
import datetime
import json
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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

━━━━━━━━━━━━━━━━━━━━━━━
SOBRE A YASMIN
━━━━━━━━━━━━━━━━━━━━━━━
Yasmin Gomes é lashista especializada em extensão de cílios, com anos de experiência.
Atende de forma personalizada, garantindo conforto, durabilidade e resultado que
combina com o estilo de cada cliente.
- Responda sobre a Yasmin APENAS com base nessa descrição.
- NUNCA invente informações pessoais, história ou características que não estejam aqui.
- NUNCA mencione redes sociais, telefones, endereços ou qualquer dado de contato
  que não esteja descrito neste prompt. Se perguntarem, diga:
  "Não tenho essa informação, mas você pode perguntar diretamente à Yasmin 😊"

━━━━━━━━━━━━━━━━━━━━━━━
SERVIÇOS E VALORES
━━━━━━━━━━━━━━━━━━━━━━━
- Volume Egípcio   — R$ 130 | 2h a 2h30
- Volume 5D        — R$ 140 | 2h30 a 3h
- Volume Mega 5D   — R$ 160 | 2h a 2h30
- Volume Brasileiro — R$ 100 | 3h a 3h30
- Manutenção       — R$ 110 | 1h a 1h30 (qualquer procedimento)
- Retirada         — 30 min

A Retirada NÃO entra na lista de serviços. Só mencione se perguntarem diretamente.

━━━━━━━━━━━━━━━━━━━━━━━
REGRAS DO ESTÚDIO
━━━━━━━━━━━━━━━━━━━━━━━
- Atendimento: segunda a sábado, das 09h às 18h. Domingo é folga.
- NUNCA confirme ou sugira horários antes das 09h ou após as 18h.
  Se o cliente pedir esse horário, diga que não atendemos nesse período.
- Intervalo de 30 minutos entre clientes.
- Agendamento com no mínimo 1 dia de antecedência. Não agendamos para o mesmo dia.
- É cobrado um sinal para confirmar o horário.
- Sexta e sábado costumam lotar; terça e quarta são mais tranquilos.

━━━━━━━━━━━━━━━━━━━━━━━
PROMOÇÃO
━━━━━━━━━━━━━━━━━━━━━━━
- Terça e quarta têm 30% de desconto em TODOS os serviços.
- Se o dia pedido tiver horário livre, agende normalmente. Nunca empurre para outro dia.
- Só ofereça terça/quarta com desconto quando o dia pedido estiver LOTADO.
- O desconto de 30% é real. NUNCA diga que não há desconto.

━━━━━━━━━━━━━━━━━━━━━━━
ESTILO DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━
- Seja breve e direta: no máximo 3 linhas por resposta conversacional.
- Nunca despeje todas as informações de uma vez.
- Para perguntas sobre um serviço específico, fale só sobre ele.
- Se não souber algo, diga que vai confirmar com a Yasmin. NUNCA invente.
- Nunca diga que uma informação foi mencionada antes. Repita-a naturalmente se preciso.
- Ao mencionar datas, use sempre o formato DD/MM. Não fale o dia da semana.
- Se o cliente fizer mais de uma pergunta, responda todas de forma organizada.
- Se o cliente reclamar ou demonstrar insatisfação, reconheça com empatia primeiro.
  Exemplo: "Sinto muito pela experiência! Como posso ajudar? 💕"
- Se a primeira mensagem da conversa for vaga ("Sim", "Ok", "Oi" sem contexto),
  responda: "Olá! Como posso te ajudar hoje? 💕"
  Em respostas dentro de uma conversa, interprete "Sim" e "Ok" como confirmação
  do que foi dito antes.

Ao listar serviços, use exatamente este formato:

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


 CONSULTA DE AGENDA

Quando o cliente quiser SABER os horários disponíveis, retorne ÚNICA E EXCLUSIVAMENTE:
DISPONIBILIDADE_JSON: {"date": "YYYY-MM-DD"}
  Se o cliente confirmar que quer ver horários de uma data específica 
  que já foi mencionada, gere o DISPONIBILIDADE_JSON para essa data imediatamente.

Nenhum texto antes ou depois. Apenas a tag.

Correto:   DISPONIBILIDADE_JSON: {"date": "2026-06-10"}
Errado:    Claro! Vou verificar. DISPONIBILIDADE_JSON: {"date": "2026-06-10"}

 AGENDAMENTO

Para marcar um horário, você precisa de TODOS os 4 dados:
1. Nome do cliente
2. Serviço desejado
3. Data
4. Horário

Se faltar algum, pergunte pelo que falta (um de cada vez). NUNCA invente nenhum dado.
NUNCA preencha o campo "name" com "nome do cliente", "cliente" ou qualquer placeholder.
Se não tiver o nome real, PERGUNTE antes de gerar o JSON.

Quando tiver os 4 dados, retorne ÚNICA E EXCLUSIVAMENTE:
AGENDAR_JSON: {"date": "YYYY-MM-DD", "time": "HH:MM", "service": "nome", "name": "nome real"}

Nenhum texto antes ou depois. Gere o JSON IMEDIATAMENTE ao ter os 4 dados.

Correto:   AGENDAR_JSON: {"date": "2026-06-10", "time": "14:00", "service": "Volume Egípcio", "name": "Maria Silva"}


LIMITAÇÃO DE ESCOPO

- Você é exclusiva do estúdio Lash Yasmin Gomes.
- Nunca responda sobre política, religião, programação, esportes ou qualquer assunto
  fora de beleza, estética, cílios e agendamentos.
- Se perguntarem algo fora do escopo, diga educadamente que você é focada apenas
  nos serviços do estúdio.
"""


@app.route("/")
def index():
    return render_template("index.html")


# ── Lógica de IA separada para o LangSmith rastrear com input/output limpos ──

@traceable
def gerar_resposta(mensagem, historico_frontend):
    historico_recente = historico_frontend[-10:]
    fuso = pytz.timezone('America/Sao_Paulo')
    data_hoje = datetime.datetime.now(fuso).strftime('%d/%m/%Y')
    data_hoje_iso = datetime.datetime.now(fuso).strftime('%Y-%m-%d')
    prompt_com_data = SYSTEM_PROMPT + \
        f"\n- Hoje é dia {data_hoje} ({data_hoje_iso})."

    mensagens = [{"role": "system", "content": prompt_com_data}
                 ] + historico_recente
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
                data_pedida = datetime.datetime.strptime(
                    date_str, "%Y-%m-%d").date()
                dias = (data_pedida - datetime.date.today()).days

                if dias < 1:
                    data_minima = datetime.date.today() + datetime.timedelta(days=1)
                    novo_texto = (
                        f"Não agendamos para o mesmo dia 💕 "
                        f"A data mais próxima disponível é {data_minima.strftime('%d/%m/%Y')}. "
                        f"Quer ver os horários disponíveis?"
                    )
                    return {"resposta": novo_texto}

                slots = get_available_slots(date_str)

                if slots:
                    novo_texto = f"✨ Horários disponíveis para {date_str}: {', '.join(slots)}. Qual desses prefere?"
                else:
                    novo_texto = (
                        f"Poxa, não temos horários livres para {date_str}. 😕 "
                        f"Que tal terça ou quarta? São mais tranquilos e ainda têm 30% de desconto! "
                        f"Me diz outro dia que eu verifico."
                    )

                return {"resposta": novo_texto}
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
                hora = int(dados['time'].split(':')[0])
                if hora < 9 or hora >= 18:
                    return {
                        "resposta": "Nosso horário de atendimento é das 9h às 18h 💕 Qual horário dentro desse período você prefere?"
                    }
                create_event(
                    date_str=dados['date'],
                    time_str=dados['time'],
                    service=dados['service'],
                    client_name=dados['name']
                )
                data_formatada = datetime.datetime.strptime(
                    dados['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
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
        conversation_id = data.get("conversation_id", "sem-id")
        return jsonify(gerar_resposta(mensagem, historico_frontend, langsmith_extra={"metadata": {"conversation_id": conversation_id}}))
    except Exception as e:
        print(f"Erro geral na IA: {e}")
        return jsonify({"erro": "IA indisponível. Tente novamente."}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("DEBUG", "true") == "true")
