const story = document.querySelector("#story");
const fileBody = document.querySelector("#file-body");
const fileEmpty = document.querySelector("#file-empty");
const fileTitle = document.querySelector("#file-title");
const thread = document.querySelector("#thread");
const more = document.querySelector("#more");
const extra = document.querySelector("#extra");
const hint = document.querySelector("#hint");

let language = "en";
let turns = [];

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function money(amount) {
  if (amount == null) return "";
  const raw = String(amount);
  if (raw.length <= 3) return `Rs ${raw}`;
  const head = raw.slice(0, -3);
  const tail = raw.slice(-3);
  const parts = [];
  let left = head;
  while (left.length > 2) {
    parts.unshift(left.slice(-2));
    left = left.slice(0, -2);
  }
  if (left) parts.unshift(left);
  return `Rs ${parts.join(",")},${tail}`;
}

function setLanguage(next) {
  language = next;
  document.querySelectorAll(".lang button").forEach((button) => {
    button.classList.toggle("on", button.dataset.lang === next);
  });
  story.placeholder = next === "hi"
    ? "जो हुआ वह अपनी भाषा में बताइए. शहर, रकम, और आपके पास क्या सबूत है."
    : "Tell it in the words you would use with a friend. City, amount, what you have as proof.";
}

document.querySelectorAll(".lang button").forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.lang));
});

async function loadSamples() {
  const response = await fetch("/api/samples");
  const samples = await response.json();
  const box = document.querySelector("#samples");
  samples.forEach((sample) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = sample.title;
    button.addEventListener("click", () => {
      setLanguage(sample.language);
      turns = [sample.text];
      story.value = sample.text;
      renderThread();
      submit();
    });
    box.appendChild(button);
  });
}

function renderThread() {
  thread.hidden = turns.length === 0;
  thread.innerHTML = turns.map((turn) => `<div class="bubble">${esc(turn)}</div>`).join("");
  more.hidden = turns.length === 0;
}

async function submit() {
  const text = turns.join("\n");
  if (!text.trim()) return;
  hint.textContent = "Reading…";
  const response = await fetch("/api/case", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  const result = await response.json();
  hint.textContent = "Facts are on the right. Fix one, then add it below. The notice is a draft.";
  render(result);
}

function factItems(facts) {
  const rows = [];
  const add = (label, value) => {
    if (value) rows.push(`<div><span>${esc(label)}</span>${esc(value)}</div>`);
  };
  add("Place", [facts.city, facts.state].filter(Boolean).join(", "));
  add("Other side", facts.other_party);
  add("Deposit", money(facts.deposit));
  add("Rent", money(facts.rent));
  add("In-hand", money(facts.wages));
  add("CTC ignored", money(facts.ctc_ignored));
  add("Paid", money(facts.consideration));
  add("Unpaid months", facts.unpaid_months);
  add("Forum", facts.forum);
  if (facts.proofs && facts.proofs.length) add("Proof named", facts.proofs.join(", "));
  if (facts.dates && facts.dates.length) add("Dates heard", facts.dates.join("; "));
  return rows.join("");
}

function render(result) {
  fileTitle.textContent = result.title || "Case file";
  fileEmpty.hidden = true;
  fileBody.hidden = false;
  const facts = factItems(result.facts || {});
  const missing = (result.missing || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const quotes = (result.statutes || []).map((row) => `
    <blockquote class="quote ${row.in_notice ? "" : "off"}">
      <strong>${esc(row.citation)}</strong> · ${esc(row.act)}
      <br />${esc(row.quote)}
      <span class="meta">${row.in_notice ? "Used in the notice." : "Shown, and kept out of the notice."} ${esc(row.source)}</span>
    </blockquote>`).join("");
  const refused = (result.refused || []).map((row) => `
    <div class="refused"><strong>${esc(row.label)}</strong><br />${esc(row.reason)}
      ${row.quote ? `<blockquote class="quote off">${esc(row.quote)}</blockquote>` : ""}
    </div>`).join("");
  const options = (result.options || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const opponent = (result.opponent || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const checks = (result.checks || []).map((item) => `<li>${esc(item)}</li>`).join("");
  const draft = result.rejected_draft ? `
    <div class="block">
      <h3>A draft that was thrown away</h3>
      <div class="rejected">
        <span class="stamp">Rejected</span>
        <p>${esc(result.rejected_draft.text)}</p>
        <div>${esc(result.rejected_draft.note)}</div>
        <ul>${result.rejected_draft.problems.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
      </div>
    </div>` : "";
  fileBody.innerHTML = `
    <div class="stamp">${result.notice ? "Draft, not advice" : "No notice"}</div>
    <div class="block"><p>${esc(result.explanation || "")}</p></div>
    ${facts ? `<div class="block"><h3>What I heard</h3><div class="facts">${facts}</div></div>` : ""}
    ${missing ? `<div class="block"><h3>Still missing</h3><ul>${missing}</ul></div>` : ""}
    ${quotes ? `<div class="block"><h3>Quotes I can point at</h3>${quotes}</div>` : ""}
    ${refused ? `<div class="block"><h3>Opened, then not used</h3>${refused}</div>` : ""}
    ${options ? `<div class="block"><h3>What you can do next</h3><ul>${options}</ul></div>` : ""}
    ${result.lawyer ? `<div class="block"><h3>When a real lawyer is the next step</h3><p>${esc(result.lawyer)}</p></div>` : ""}
    ${opponent ? `<div class="block"><h3>The other side will say</h3><ul>${opponent}</ul></div>` : ""}
    ${result.notice ? `<div class="block"><h3>Notice</h3><button type="button" id="copy" class="ghost">Copy</button><pre class="notice" id="notice">${esc(result.notice)}</pre></div>` : ""}
    ${draft}
    <div class="block checks"><h3>How this file was checked</h3><ul>${checks}</ul></div>
  `;
  const copy = document.querySelector("#copy");
  if (copy) {
    copy.addEventListener("click", async () => {
      await navigator.clipboard.writeText(result.notice);
      copy.textContent = "Copied";
    });
  }
}

document.querySelector("#send").addEventListener("click", () => {
  const text = story.value.trim();
  if (!text) return;
  turns = [text];
  renderThread();
  submit();
});

more.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = extra.value.trim();
  if (!text) return;
  turns.push(text);
  extra.value = "";
  renderThread();
  submit();
});

const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
const mic = document.querySelector("#mic");
if (!Speech) {
  mic.disabled = true;
  mic.textContent = "No mic";
} else {
  const rec = new Speech();
  rec.onresult = (event) => {
    const said = event.results[0][0].transcript;
    story.value = `${story.value} ${said}`.trim();
  };
  rec.onerror = () => { hint.textContent = "The microphone did not catch that. Type it instead."; };
  mic.addEventListener("click", () => {
    rec.lang = language === "hi" ? "hi-IN" : "en-IN";
    rec.start();
    hint.textContent = "Listening…";
  });
}

loadSamples();
