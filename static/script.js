const input = document.getElementById("user-input");
const container = document.getElementById("chat-container");
const typing = document.getElementById("typing");

input.addEventListener("keydown", e => {
  if (e.key === "Enter") enviar();
});

async function enviar() {
  const msg = input.value.trim();
  if (!msg) return;

  addMessage(msg, "user");
  input.value = "";
  typing.style.display = "block";
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensagem: msg })
    });

    const data = await res.json();
    typing.style.display = "none";
    addMessage(data.resposta, "agent");
  } catch (err) {
    typing.style.display = "none";
    addMessage("Erro ao conectar com o agente. Tente novamente.", "agent");
  }
}

function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  if (type === "agent") {
    div.innerHTML = `<div class="sender">Lash IA</div>${text}`;
  } else {
    div.textContent = text;
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}