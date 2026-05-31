const chatWidget   = document.getElementById('chatWidget');
const chatWelcome  = document.getElementById('chatWelcome');
const chatMessages = document.getElementById('chatMessages');
const chatTyping   = document.getElementById('chatTyping');
const chatInput    = document.getElementById('chatInput');
const chatBody     = document.getElementById('chatBody');

let isMaximized = false;

// ── Toggle open/close ──
function toggleChat() {
  chatWidget.classList.toggle('open');
}

// ── Maximize / restore ──
function maximizeChat() {
  isMaximized = !isMaximized;
  chatWidget.classList.toggle('maximized', isMaximized);
}

// ── Reset conversation ──
function resetChat() {
  chatMessages.innerHTML = `
    <div class="message agent">
      <div class="sender">Lash IA</div>
      Olá! Como posso te ajudar hoje? 🌸
    </div>`;
  chatWelcome.style.display  = 'flex';
  chatMessages.style.display = 'none';
  chatInput.value = '';
}

// ── Quick buttons ──
function quickSend(text) {
  chatWelcome.style.display  = 'none';
  chatMessages.style.display = 'flex';
  sendMessage(text);
}

// ── Send message ──
async function sendMessage(text) {
  const msg = text || chatInput.value.trim();
  if (!msg) return;

  // Show messages panel
  chatWelcome.style.display  = 'none';
  chatMessages.style.display = 'flex';

  addMessage(msg, 'user');
  chatInput.value = '';
  chatTyping.style.display = 'block';
  scrollBottom();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensagem: msg })
    });
    const data = await res.json();
    chatTyping.style.display = 'none';
    addMessage(data.resposta, 'agent');
  } catch (err) {
    chatTyping.style.display = 'none';
    addMessage('Ops! Não consegui conectar. Tente novamente.', 'agent');
  }
}

// ── Add message to DOM ──
function addMessage(text, type) {
  const div = document.createElement('div');
  div.className = `message ${type}`;
  if (type === 'agent') {
    div.innerHTML = `<div class="sender">Lash IA</div>${text}`;
  } else {
    div.textContent = text;
  }
  chatMessages.appendChild(div);
  scrollBottom();
}

// ── Scroll to bottom ──
function scrollBottom() {
  chatBody.scrollTop = chatBody.scrollHeight;
}
