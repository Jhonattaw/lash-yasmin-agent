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
- Explicar a política de agendamento e sinal
- Sugerir terça e quarta com 30% de desconto quando o dia pedido está cheio
- Manter contexto da conversa

## Tecnologias
- Python 3.11
- Flask (interface web)
- Ollama + Mistral 7B (modelo local, 100% offline)
- python-dotenv
- HTML, CSS e JavaScript

## Como rodar

1. Instale o Ollama em ollama.com e baixe o modelo:
ollama pull mistral:7b

2. Clone o repositório:
git clone https://github.com/Jhonattaw/lash-yasmin-agent
cd lash-yasmin-agent

3. Crie o ambiente virtual:
py -3.11 -m venv venv
venv\Scripts\activate
pip install ollama flask python-dotenv

4. Crie o arquivo .env na raiz:
OLLAMA_MODEL=mistral:7b

5. Rode a aplicação:
python src/app.py

6. Acesse no navegador:
http://localhost:5000

## Estrutura do projeto
lash-yasmin-agent/
├── src/
│   └── app.py          # agente + servidor Flask
├── static/
│   ├── style.css       # identidade visual
│   ├── script.js       # lógica do chat
│   └── logo_cliente.png
├── templates/
│   └── index.html      # interface web
├── docs/
│   └── requisitos.md   # levantamento de requisitos
└── .env

## Próximos passos
- Integração com Google Calendar API para verificar horários reais
- Sistema de confirmação de sinal via WhatsApp API
- Deploy na Vercel com modelo via Groq API
