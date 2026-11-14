import { api, esc, fmt, setTotals, short, stamp, verdictOf } from "/assets/common.js";

const TOOL_LABEL = { invoice: "Invoice", merchant_page: "Product page", tool_output: "API reply / tool output" };
const qs = new URLSearchParams(location.search);
let levels = [], cur = null, state = { docs: {}, tool: null, busy: false, last: null };

function ledger(progress) {
  document.getElementById("ledger").innerHTML = levels.map((l) => {
    const name = l.key === "BOSS" ? "BOSS" : `LEVEL ${l.level}`;
    return `<li><a href="?level=${l.key}" ${l.key === cur.key ? 'aria-current="step"' : ""} class="${progress[l.key]?.won ? "won" : ""}">
      <b>${name}</b>${esc(l.title.replace(/^The /, ""))}</a></li>`;
  }).join("");
}

function brief(l) {
  const a = l.agent;
  const after = /added after lock/.test(l.defence) ? ' <span class="tag-after">added after lock</span>' : "";
  return `<aside class="card" aria-labelledby="brief-h">
    <p class="eyebrow">${l.key === "BOSS" ? "Boss level" : `Level ${l.level}`} · Brief</p>
    <h1 id="brief-h" style="font-size:24px">${esc(l.title)}</h1>
    <p class="muted small">${esc(l.modelled_on)}</p>
    <p>${esc(l.brief)}</p>
    <dl class="facts">
      <dt>Works for</dt><dd>${esc(a.owner)}</dd>
      <dt>Per payment</dt><dd>${fmt(a.per_payment)}</dd>
      <dt>Per day</dt><dd>${fmt(a.per_day)}</dd>
      <dt>Human approval at</dt><dd>${fmt(a.approval_at)}</dd>
      <dt>Win at</dt><dd>${fmt(l.target)} wasted</dd>
    </dl>
    <p class="small" style="margin-top:12px"><strong>Its instructions:</strong> “${esc(l.request)}”</p>
    <p class="small muted">${l.open_payees && l.key !== "BOSS" ? "It may pay new payees." : `Payees it knows: ${esc(l.payees.join(", "))}.`}</p>
    <div class="defence"><strong>${l.key === "BOSS" ? "Defences" : "Defence added in this level"}</strong>${after}<br>${esc(l.defence.replace(/ \(added after lock\)/, ""))}</div>
    ${l.gaps.length ? `<div class="gaps" style="margin-top:16px"><strong>What AgentGuard still can't see</strong><ul>${l.gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul></div>` : ""}
    <details><summary>${l.disabled_checks.length ? `${l.disabled_checks.length} ${l.disabled_checks.length === 1 ? "check is" : "checks are"} switched off until later levels` : "No checks switched off"}</summary>
      <p class="small mono">${esc(l.disabled_checks.join(", ") || "Every check runs.")}</p>
      <p class="small muted">Policy ${esc(l.policy_version)}</p></details>
  </aside>`;
}

function composer(l) {
  state.tool = state.tool || l.tools[0];
  const tabs = l.tools.length > 1 ? `<div class="tabs" role="tablist" aria-label="Document type">${l.tools.map((t) =>
    `<button class="tab" role="tab" aria-selected="${t === state.tool}" data-tool="${t}">${TOOL_LABEL[t] || t}</button>`).join("")}</div>` : "";
  return `<div class="card">
    <p class="eyebrow">Your attack</p>
    <h2 style="font-size:20px">Write the ${(TOOL_LABEL[state.tool] || "document").toLowerCase()} the agent will read</h2>
    <div class="chips" role="group" aria-label="Templates">${l.templates.map((t, i) =>
      `<button class="chip" data-tpl="${i}" aria-pressed="false">${esc(t.name)}</button>`).join("")}</div>
    ${tabs}
    <div class="field"><label for="doc">${TOOL_LABEL[state.tool] || "Document"} text</label>
      <textarea id="doc" maxlength="2000" placeholder="Write what the agent will read…">${esc(state.docs[state.tool] || "")}</textarea>
      <p class="hint"><span id="count">0</span> of 2,000 characters. Don't include personal information.</p></div>
    <div class="actions"><button class="btn btn-p full-m" id="send">Send to agent <kbd>Ctrl ↵</kbd></button>
      <span class="hint" id="tries"></span></div>
    <div id="err" role="alert"></div>
  </div>
  <div id="result" aria-live="polite"></div>`;
}

const named = (text, rows) => text.replace(/\bm_[a-z0-9_]+\b/g, (id) => {
  const hit = (cur.payee_ids || {})[id]; return hit || id; });

function decisive(rows) {
  return rows.find((r) => r.waste && !r.settled) || rows.find((r) => !r.settled) || rows[rows.length - 1];
}

function summarise(rows) {
  const g = new Map();
  for (const r of rows) {
    const k = `${r.payee}|${r.amount}|${r.outcome}|${r.reason}`;
    const e = g.get(k) || { ...r, n: 0, wasteSum: 0 };
    e.n += 1; e.wasteSum += r.waste; g.set(k, e);
  }
  return [...g.values()];
}

function resultCard(data) {
  const res = data.result, att = res.attempts[res.attempts.length - 1], rows = att.rows;
  const a = data.attempt || (data.attempts && data.attempts[data.attempts.length - 1]);
  if (!rows.length) {
    return `<div class="card" style="margin-top:16px"><p class="eyebrow">Attempt ${att.n + 1}</p><h2 style="font-size:20px">The agent didn't bite</h2>
      <p>It proposed no payment. ${esc(a?.note || "")}</p><p class="muted small">That is the agent being cautious, not AgentGuard. Try a document it will believe.</p></div>`;
  }
  const d = decisive(rows), v = verdictOf(d.outcome);
  const bit = rows.some((r) => r.waste);
  const caught = rows.filter((r) => r.waste && !r.settled).reduce((s, r) => s + r.waste, 0);
  const lost = rows.filter((r) => r.waste && r.settled).reduce((s, r) => s + r.waste, 0);
  const pct = Math.min(100, Math.round(100 * res.wasted / cur.target));
  const why = v === "approved"
    ? `<div class="why approved"><p><strong>It went through.</strong> Every check this level runs passed. ${lost ? `${fmt(lost)} of wasted money settled.` : "Nothing wasted yet."}</p></div>`
    : `<div class="why ${v}"><p><strong>Why it was ${v}:</strong> ${d.reason === "APPROVAL_REQUIRED"
        ? `${fmt(d.amount)} is at or above the ${fmt(cur.agent.approval_at)} approval threshold, so a person must approve it.` : esc(named(d.detail))}</p>${v === "held" ? "<p>A person now has to approve or reject it in the approval system. Text in a document can't do that.</p>" : ""}</div>`;
  const rowsHtml = summarise(rows).map((r) => `<tr><td>${stamp(verdictOf(r.outcome), true)}</td><td>${esc(r.payee)}</td>
     <td class="n">${r.n > 1 ? `${r.n} × ` : ""}${fmt(r.amount)}</td><td class="mono small">${esc(r.reason)}</td><td class="n">${r.wasteSum ? fmt(r.wasteSum) : "—"}</td></tr>`).join("");
  const aud = rows.filter((r) => r.audit).slice(-6).map((r, i, arr) =>
    `<li class="${i === arr.length - 1 ? "new" : ""}">#${r.audit.seq} · DECISION · ${esc(r.outcome)} · ${esc(r.reason)} · ${fmt(r.amount)} → ${esc(r.payee)}<br>prev ${short(r.audit.prev)} · hash ${short(r.audit.hash)}</li>`).join("");
  return `<div class="card" style="margin-top:16px">
    <p class="eyebrow">Attempt ${att.n + 1} · result</p>
    <div class="result-head"><div>
      <h2 style="font-size:20px">${bit ? "The agent took the bait" : "The agent didn't bite: it bought only what was asked"}</h2>
      <p style="margin:0">${rows.length === 1 ? `It proposed paying ${esc(d.payee)}` : `It proposed ${rows.length} payments`}${a?.note ? `<br><span class="muted small">Agent's note: “${esc(a.note)}”</span>` : ""}</p>
      <div class="num" style="font-size:28px;font-weight:600">${fmt(rows.reduce((s, r) => s + r.amount, 0))}</div>
      <p class="hint">Decision ${esc(d.decision_id)} · ${d.ms} ms <span class="src">MEASURED</span></p></div>
      <div class="verdict">${stamp(v)}<div class="code ${v}" style="margin-top:8px">${esc(d.reason)}</div></div></div>
    ${why}
    <div class="tablewrap" style="margin-top:12px"><table class="t rows"><thead><tr><th>Verdict</th><th>Payee</th><th class="n">Amount</th><th>Reason code</th><th class="n">Wasted</th></tr></thead><tbody>${rowsHtml}</tbody></table></div>
    <div class="stats" style="margin-top:16px">
      <div class="stat"><div class="k">Money protected this try</div><div class="n">${fmt(caught)}</div></div>
      <div class="stat"><div class="k">Wasted so far this level</div><div class="n">${fmt(res.wasted)} <span class="small muted">of ${fmt(cur.target)}</span></div><div class="target" aria-hidden="true"><i style="width:${pct}%"></i></div></div>
    </div>
    <div class="audit"><p class="eyebrow" style="margin-top:16px">Audit log · hash-chained · ${res.audit_verified ? "chain verified ✓" : "CHAIN BROKEN"}</p><ol>${aud}</ol></div>
    ${res.alerts?.length ? `<p class="small" style="margin-top:8px"><strong>AML monitoring:</strong> ${res.alerts.map((x) => esc(x.rule)).join(", ")}</p>` : ""}
    ${res.won ? winPanel(data) : `<div class="actions" style="margin-top:12px"><button class="btn btn-p" id="again">Try another attack <kbd>R</kbd></button><button class="btn btn-s" id="reset">Start this level over</button></div>`}
  </div>`;
}

function winPanel(data) {
  const rv = data.reveal || [];
  const list = rv.map((x) => `<li><strong>${esc(x.label)}:</strong> ${x.first_catch
    ? `${stamp(verdictOf(x.first_catch.outcome), true)} <span class="mono small">${esc(x.first_catch.reason)}</span> on ${fmt(x.first_catch.amount)} to ${esc(x.first_catch.payee)}`
    : x.stopped ? "stopped" : '<span class="code blocked">would not stop this</span>'}</li>`).join("");
  const none = rv.length && rv.every((x) => !x.first_catch);
  return `<div class="why approved" style="margin-top:16px"><h3>You beat level ${cur.key === "BOSS" ? "Boss" : cur.level}: ${fmt(data.result.wasted)} wasted.</h3>
    <p>${esc(cur.lesson)}</p>
    ${rv.length ? `<p><strong>Which defence would have stopped you?</strong> Your exact payments, re-run:</p><ul class="reveal">${list}</ul>` : ""}
    ${none ? "<p><strong>No current defence stops this.</strong> That is a real gap, and the most useful kind of attack to share.</p>" : ""}</div>
    <div class="card" style="margin-top:12px" id="consent-box">
      <label class="chk"><input type="checkbox" id="consent"> <span><strong>Let AgentGuard learn from my attack.</strong> Store the text of this attack for a future visitor-submitted test set. It contains no personal information.</span></label>
      <p class="hint">Text only. No name, email or IP address. Reviewed by a person before use. You get an ID to request deletion. <a href="/privacy">What we keep</a></p>
      <div class="actions"><button class="btn btn-s" id="donate">Save my choice</button>${cur.key !== "BOSS" ? `<a class="btn btn-p" href="?level=${levels[levels.findIndex((l) => l.key === cur.key) + 1].key}">Next level <kbd>N</kbd></a>` : ""}<button class="btn btn-s" id="reset">Play this level again</button></div>
      <div id="donate-msg" role="status"></div></div>`;
}

function bind() {
  const doc = document.getElementById("doc"), count = document.getElementById("count");
  const sync = () => { state.docs[state.tool] = doc.value; count.textContent = doc.value.length.toLocaleString(); };
  doc.addEventListener("input", sync); sync();
  document.querySelectorAll("[data-tpl]").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("[data-tpl]").forEach((x) => x.setAttribute("aria-pressed", x === b));
    doc.value = cur.templates[+b.dataset.tpl].text; sync(); doc.focus();
  }));
  document.querySelectorAll("[data-tool]").forEach((b) => b.addEventListener("click", () => { state.tool = b.dataset.tool; render(); }));
  document.getElementById("send").addEventListener("click", send);
  doc.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") send(); });
}

function bindResult() {
  document.getElementById("again")?.addEventListener("click", () => { document.getElementById("doc").focus(); scrollTo({ top: 0, behavior: "smooth" }); });
  document.getElementById("reset")?.addEventListener("click", async () => { await api("/api/reset", { level: cur.key }); state.last = null; load(); });
  document.getElementById("donate")?.addEventListener("click", async () => {
    const msg = document.getElementById("donate-msg");
    if (!document.getElementById("consent").checked) { msg.innerHTML = '<p class="hint">Nothing stored. Thanks for playing.</p>'; return; }
    const r = await api("/api/donate", { level: cur.key, consent: true });
    msg.innerHTML = r.error ? `<p class="banner err">${esc(r.error)}</p>`
      : `<p class="banner">Thank you. Submission ID <span class="mono">${esc(r.submission_id)}</span>. Keep it to ask for deletion.</p>`;
  });
}

async function send() {
  if (state.busy) return;
  const btn = document.getElementById("send"), err = document.getElementById("err");
  state.busy = true; btn.disabled = true; btn.innerHTML = '<span class="spinner" aria-hidden="true"></span> The agent is reading…'; err.innerHTML = "";
  const docs = {}; for (const t of cur.tools) docs[t] = state.docs[t] || "";
  const r = await api("/api/attempt", { level: cur.key, documents: docs });
  state.busy = false;
  if (r.error) { btn.disabled = false; btn.innerHTML = "Send to agent <kbd>Ctrl ↵</kbd>"; err.innerHTML = `<p class="banner err" style="margin-top:12px">${esc(r.error)}</p>`; return; }
  state.last = r; setTotals(r.vault);
  document.getElementById("tries").textContent = `${r.tries_left} of 30 tries left today`;
  btn.disabled = false; btn.innerHTML = "Send to agent <kbd>Ctrl ↵</kbd>";
  document.getElementById("result").innerHTML = resultCard(r); bindResult();
  document.getElementById("result").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}

function render() {
  document.getElementById("main").innerHTML = brief(cur) + `<section aria-label="Attack">${composer(cur)}</section>`;
  bind();
  if (state.last) { document.getElementById("result").innerHTML = resultCard(state.last); bindResult(); }
}

async function load() {
  const all = await api("/api/levels");
  if (all.error) { document.getElementById("main").innerHTML = `<p class="banner err">${esc(all.error)}</p>`; return; }
  levels = all.levels; setTotals(all.vault);
  cur = levels.find((l) => l.key === (qs.get("level") || "L1")) || levels[0];
  const st = await api(`/api/level/${cur.key}`);
  const progress = all.progress;
  if (st.result) { progress[cur.key].won = st.result.won; state.last = { result: st.result, attempts: st.attempts, reveal: st.reveal }; }
  ledger(progress); render();
  document.getElementById("tries").textContent = `${all.tries_left} of 30 tries left today`;
  document.title = `${cur.title} · Break the bank`;
}

addEventListener("keydown", (e) => {
  if (e.target.matches("textarea, input")) return;
  if (e.key === "r" || e.key === "R") document.getElementById("doc")?.focus();
  if ((e.key === "n" || e.key === "N") && state.last?.result?.won) { const i = levels.findIndex((l) => l.key === cur.key); if (levels[i + 1]) location.search = `?level=${levels[i + 1].key}`; }
});
load();
