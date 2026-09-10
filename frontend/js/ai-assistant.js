const chat = document.querySelector("#chat"),
  form = document.querySelector("#chatForm"),
  message = document.querySelector("#message");
function add(text, who) {
  const d = document.createElement("div");
  d.className = `bubble ${who}`;
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}
document.querySelectorAll(".suggestions button").forEach(
  (b) =>
    (b.onclick = () => {
      message.value = b.textContent;
      message.focus();
    }),
);
form.onsubmit = async (e) => {
  e.preventDefault();
  const text = message.value.trim();
  if (!text) return;
  add(text, "user");
  message.value = "";
  add("Thinking…", "ai");
  const pending = chat.lastChild;
  try {
    const r = await apiPost("/api/ai/chat", { message: text });
    pending.textContent = r.answer;
  } catch (err) {
    pending.textContent =
      "FinAI is unavailable. Check the backend configuration.";
  }
};
