# Lash Yasmin Gomes — Agente de Agendamento com IA

Agente conversacional com interface web desenvolvido para o estúdio
de extensão de cílios Lash Yasmin Gomes.

Projeto criado para demonstrar como Inteligência Artificial pode
resolver problemas reais de pequenos negócios — combinando
levantamento de requisitos, gestão de produto e engenharia de IA.

## O Problema de Negócio

A profissional atende sozinha e não consegue responder o WhatsApp
durante os procedimentos. Isso gera perda de clientes, agenda
desorganizada e sobrecarga nos fins de semana.

**Dores mapeadas:**
- Clientes somem sem confirmar horário
- Sexta e sábado lotam, terça e quarta ficam vazias
- Sem canal automatizado de atendimento

## A Solução

Agente de IA treinado com as regras de negócio do estúdio, capaz de:
- Informar serviços, duração e valores
- Consultar horários disponíveis em tempo real via Google Calendar API
- Sugerir terça e quarta com 30% de desconto quando o dia pedido está cheio
- Manter contexto da conversa com histórico stateless no frontend
- Recusar perguntas fora do escopo do estúdio

## Tecnologias
- Python 3.11
- Flask (servidor web)
- Ollama + Mistral 7B (modelo de linguagem rodando localmente)
- Google Calendar API (consulta de horários reais)
- LangSmith (observabilidade e tracing das conversas do agente)
- python-dotenv
- pytz (fuso horário América/São Paulo)
- HTML, CSS e JavaScript

## Decisões Técnicas
- **Histórico stateless no frontend (`skip_history`):** respostas de horários não contaminam o contexto da conversa.
- **Tag `DISPONIBILIDADE_JSON`:** o modelo sinaliza a intenção de agendamento numa única chamada, sem uma segunda ida ao LLM.
- **Data injetada dinamicamente no system prompt:** o agente sabe a data de hoje e entende "amanhã", "essa sexta", etc.
- **Lógica de IA isolada em `gerar_resposta()` com `@traceable`:** permite observar cada conversa no LangSmith (entrada, saída, latência) sem misturar com a camada web.
- **Fuso `America/Sao_Paulo` com pytz:** horários sempre no horário do estúdio.

## Observabilidade

As conversas do agente são rastreadas com LangSmith. Cada mensagem
gera um trace com a entrada do usuário, a resposta gerada e o tempo
de processamento — o que permite depurar comportamentos e, no futuro,
avaliar a qualidade das respostas de forma sistemática.

## Arquitetura

```
lash-yasmin-agent/
├── src/
│   └── app.py               # servidor Flask + orquestração (função gerar_resposta com @traceable)
├── services/
│   └── calendar_service.py  # integração Google Calendar API
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html
├── docs/
│   └── requisitos.md        # levantamento de requisitos do negócio
├── credentialsg.json        # credenciais Google (não commitado)
├── requirements.txt
└── .env
```

## Como rodar

1. Instale o Ollama em ollama.com e baixe o modelo:
```
ollama pull mistral:7b
```

2. Clone o repositório:
```
git clone https://github.com/Jhonattaw/lash-yasmin-agent
cd lash-yasmin-agent
```

3. Crie o ambiente virtual e instale as dependências:
```
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

4. Configure as credenciais do Google Calendar:
- Crie um projeto no Google Cloud Console
- Ative a Google Calendar API
- Crie uma Service Account e baixe o JSON como `credentialsg.json` na raiz
- Compartilhe a agenda da Yasmin com o e-mail da Service Account

5. Crie o arquivo `.env` na raiz:
```
OLLAMA_MODEL=mistral:7b

# Observabilidade (opcional — sem isso o app roda igual, só sem tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua_chave_lsv2_aqui
LANGSMITH_PROJECT=lash-yasmin-agent
```

6. Rode a aplicação:
```
python src/app.py
```

7. Acesse no navegador:
```
http://localhost:5000
```

## Próximos passos
- Trocar Ollama por Groq API para respostas em 1-2 segundos
- Deploy na Vercel com link público
- Permitir que o agente crie o evento no Google Calendar (hoje apenas consulta)
- Confirmação de sinal via WhatsApp API (Twilio)