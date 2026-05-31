const chatWidget   = document.getElementById('chatWidget');
const chatWelcome  = document.getElementById('chatWelcome');
const chatMessages = document.getElementById('chatMessages');
const chatTyping   = document.getElementById('chatTyping');
const chatInput    = document.getElementById('chatInput');
const chatBody     = document.getElementById('chatBody');
const chatLauncher = document.getElementById('chatLauncher');

let isMaximized = false;
let isSending   = false;
let chatHistory = [];

function toggleChat() {
  chatWidget.classList.toggle('open');
   chatLauncher.style.display  = 
    chatWidget.classList.contains('open') ? 'none' : 'flex';
    
}

function maximizeChat() {
  isMaximized = !isMaximized;
  chatWidget.classList.toggle('maximized', isMaximized);
  
}

function resetChat() {
  chatHistory = [];
  chatMessages.innerHTML = '';
  addMessage('Olá! Como posso te ajudar hoje? 🌸', 'agent');
  chatWelcome.style.display  = 'flex';
  chatMessages.style.display = 'none';
  chatInput.value = '';
}

function quickSend(text) {
  chatWelcome.style.display  = 'none';
  chatMessages.style.display = 'flex';
  sendMessage(text);
}

async function sendMessage(text) {
  if (isSending) return;

  const msg = text || chatInput.value.trim();
  if (!msg) return;

  chatWelcome.style.display  = 'none';
  chatMessages.style.display = 'flex';

  addMessage(msg, 'user');
  chatInput.value = '';
  isSending = true;
  chatTyping.style.display = 'block';
  scrollBottom();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: msg,
        historico: chatHistory
      }),
      signal: controller.signal
    });

    const data = await res.json();
    clearTimeout(timeout);

    if (data.erro) {
      addMessage(data.erro, 'agent');
    } else {
      chatHistory.push({ role: 'user',      content: msg         });
      chatHistory.push({ role: 'assistant', content: data.resposta });
      addMessage(data.resposta, 'agent');
    }

  } catch (err) {
    clearTimeout(timeout);
    const msg_erro = err.name === 'AbortError'
      ? 'A resposta demorou demais. Tente novamente.'
      : 'Erro de conexão. Verifique e tente novamente.';
    addMessage(msg_erro, 'agent');
  } finally {
    isSending = false;
    chatTyping.style.display = 'none';
  }
}

function addMessage(text, type) {
  const div = document.createElement('div');
  div.className = `message ${type}`;

  if (type === 'agent') {
    const sender = document.createElement('div');
    sender.className = 'sender';
    sender.textContent = 'Lash IA';

    const content = document.createElement('div');
    content.textContent = text;

    div.appendChild(sender);
    div.appendChild(content);
  } else {
    div.textContent = text;
  }

  chatMessages.appendChild(div);
  scrollBottom();
}

function scrollBottom() {
  chatBody.scrollTop = chatBody.scrollHeight;
}