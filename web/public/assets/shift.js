import { api, esc, fmt } from "/assets/common.js";

const S = { seed: "daily", data: null, sel: 0, opened: [], decided: {}, detail: null, t0: 0, left: 0, timer: null, relaxed: false, over: false };
const main = document.getElementById("main");

function intro() {
  main.innerHTML = `<section class="card" style="margin:24px 0;max-width:760px">
    <p class="eyebrow">Analyst shift</p><h1>You have three minutes and room for 15 reviews.</h1>
    <p>Sixty alerts are waiting. Some are laundering; most are agents doing their jobs. Opening an alert uses one review and shows the evidence and the AI investigator's case note. Escalate what looks like laundering; clear the rest.</p>
    <p class="muted">Score: laundering caught, false alarms (each costs $50.00 of analyst time, an assumption), and money recovered by holding the agent early. At the end you'll see how AgentGuard's own ranked queue did with the same 15 reviews.</p>
    <label class="chk"><input type="checkbox" id="relaxed"> <span>Relaxed mode: no timer</span></label>
    <div class="actions" style="margin-top:12px"><button class="btn btn-p" id="start-daily">Start today's shift</button><button class="btn btn-s" id="start-practice">Practice shift</button></div>
  </section>`;
  document.getElementById("start-daily").onclick = () => start("daily");
  document.getElementById("start-practice").onclick = () => start(String(1 + Math.floor(Math.random() * 1e6)));
}

async function start(seed) {
  S.relaxed = document.getElementById("relaxed").checked; S.seed = seed;
  const d = await api(`/api/shift?seed=${encodeURIComponent(seed)}`);
  if (d.error) { main.innerHTML = `<p class="banner err">${esc(d.error)}</p>`; return; }
  Object.assign(S, { data: d, sel: 0, opened: [], decided: {}, detail: null, over: false, left: d.seconds });
  render();
  if (!S.relaxed) {
    S.t0 = Date.now();
    S.timer = setInterval(() => {
      if (document.hidden) { S.t0 += 1000; return; }  // pauses while the tab is hidden
      S.left = Math.max(0, S.data.seconds - Math.floor((Date.now() - S.t0) / 1000));
      const el = document.getElementById("clock"); if (el) el.textContent = clock();
      if (S.left === 0) finish();
    }, 1000);
  }
}

const clock = () => S.relaxed ? "No timer" : `${Math.floor(S.left / 60)}:${String(S.left % 60).padStart(2, "0")}`;
const used = () => S.opened.length;

function hud() {
  const esc_n = Object.values(S.decided).filter((x) => x === "escalate").length;
  return `<div class="hud" aria-live="polite">
    <div class="stat"><div class="k">${S.relaxed ? "Practice pace" : "Time left"}</div><div class="n" id="clock">${clock()}</div></div>
    <div class="stat"><div class="k">Reviews used</div><div class="n">${used()} / ${S.data.budget}</div></div>
    <div class="stat"><div class="k">Escalated</div><div class="n">${esc_n}</div></div>
    <div class="stat" style="display:flex;align-items:center"><button class="btn btn-s" id="end">End shift</button></div></div>`;
}

function queue() {
  return `<div class="card" style="padding:12px"><div class="tablewrap"><table class="t queue" role="grid" aria-label="Alert queue">
    <thead><tr><th>Rule</th><th>Sev</th><th class="hide-m">Subject</th><th class="n">Total</th><th class="n">Pays</th><th></th></tr></thead><tbody>
    ${S.data.alerts.map((a, i) => {
      const d = S.decided[a.id];
      return `<tr data-i="${i}" aria-selected="${i === S.sel}" class="${S.opened.includes(a.id) ? "done" : ""}">
        <td>${esc(a.rule)}</td><td class="sev">${a.severity}</td><td class="hide-m mono small">${esc(a.subject)}</td>
        <td class="n">${fmt(a.total)}</td><td class="n">${a.payments}</td>
        <td>${d ? `<span class="pill">${d === "escalate" ? "ESCALATED" : "CLEARED"}</span>` : S.opened.includes(a.id) ? '<span class="pill">OPEN</span>' : ""}</td></tr>`;
    }).join("")}</tbody></table></div></div>`;
}

function detail() {
  const a = S.data.alerts[S.sel];
  if (!S.opened.includes(a.id)) {
    return `<div class="card"><p class="eyebrow">Alert · ${esc(a.code)}</p><h2 style="font-size:20px">${esc(a.rule)} · severity ${a.severity}</h2>
      <p class="mono small">${esc(a.subject)} · ${a.payments} payments · ${fmt(a.total)}</p>
      <p class="muted">Opening it uses one of your ${S.data.budget} reviews.</p>
      <button class="btn btn-p" id="open" ${used() >= S.data.budget ? "disabled" : ""}>Open alert <kbd>Enter</kbd></button>
      ${used() >= S.data.budget ? '<p class="hint">No reviews left. End the shift to see your score.</p>' : ""}</div>`;
  }
  const d = S.detail && S.detail.alert.id === a.id ? S.detail : null;
  if (!d) return `<div class="card"><p class="muted"><span class="spinner" aria-hidden="true"></span> Loading evidence and case note…</p></div>`;
  const note = d.case_note;
  const noteHtml = !note ? '<p class="muted">The investigator is unavailable right now; decide from the evidence.</p>'
    : !note.sentences.length ? `<p class="muted">Every sentence of the investigator's draft was removed by the checker (${esc(Object.keys(note.dropped || {}).join(", ") || "no usable sentences")}), so only its recommendation is shown: <strong>${esc(note.recommendation || "none")}</strong>.</p>`
    : `<ol class="note">${note.sentences.map((s) => `<li>${esc(s.text.replace(/\s*\[T\d{7}\]/g, ""))} ${s.cites.map((c) => `<button class="cite" data-c="${c}">${c}</button>`).join("")}</li>`).join("")}</ol>
       <p class="small">Investigator recommends: <strong>${esc(note.recommendation || "no recommendation")}</strong>${Object.keys(note.dropped || {}).length ? ` · ${Object.values(note.dropped).reduce((x, y) => x + y, 0)} sentence(s) dropped by the checker` : ""}</p>`;
  const dec = S.decided[a.id];
  return `<div class="card"><p class="eyebrow">Alert · ${esc(a.code)}</p><h2 style="font-size:20px">${esc(a.rule)} · severity ${a.severity}</h2>
    <p><strong>Facts (computed by code):</strong> ${esc(a.explanation)}</p>
    ${d.usual_merchants.length ? `<p class="small muted">This agent usually pays: ${esc(d.usual_merchants.join(", "))}</p>` : ""}
    <h3 style="font-size:16px;margin-top:12px">AI investigator's case note</h3>${noteHtml}
    <div class="tablewrap"><table class="t stack" id="txns"><thead><tr><th>ID</th><th>Time (UTC)</th><th>Agent</th><th>Merchant</th><th class="n">Amount</th></tr></thead><tbody>
      ${d.transactions.map((t) => `<tr data-id="${t.id}"><td class="mono small" data-label="ID">${t.id}</td><td class="mono small" data-label="Time (UTC)">${t.at.slice(5, 16).replace("T", " ")}</td><td class="mono small" data-label="Agent">${esc(t.agent)}</td>
        <td data-label="Merchant"><span>${esc(t.merchant)} <span class="small muted">${esc(t.category)}${t.trusted ? "" : " · untrusted"}</span></span></td><td class="n" data-label="Amount">${fmt(t.amount)}</td></tr>`).join("")}</tbody></table></div>
    <div class="actions" style="margin-top:12px">${dec ? `<p class="banner">You ${dec === "escalate" ? "escalated" : "cleared"} this alert.</p>`
      : `<button class="btn btn-p" id="esc">Escalate <kbd>E</kbd></button><button class="btn btn-s" id="clr">Clear <kbd>C</kbd></button>`}</div></div>`;
}

function render() {
  if (S.over) return;
  main.innerHTML = hud() + `<div class="layout"><section aria-label="Queue">${queue()}</section><section id="detail" aria-label="Alert">${detail()}</section></div>`;
  main.querySelectorAll("tr[data-i]").forEach((tr) => tr.onclick = () => { S.sel = +tr.dataset.i; render(); });
  document.getElementById("open")?.addEventListener("click", openSel);
  document.getElementById("esc")?.addEventListener("click", () => decide("escalate"));
  document.getElementById("clr")?.addEventListener("click", () => decide("clear"));
  document.getElementById("end").onclick = finish;
  main.querySelectorAll(".cite").forEach((b) => b.onclick = () => {
    main.querySelectorAll("#txns tr").forEach((r) => r.classList.toggle("hl", r.dataset.id === b.dataset.c));
    main.querySelector(`#txns tr[data-id="${b.dataset.c}"]`)?.scrollIntoView({ block: "nearest" });
  });
}

async function openSel() {
  const a = S.data.alerts[S.sel];
  if (S.opened.includes(a.id) || used() >= S.data.budget) return;
  S.opened.push(a.id); S.detail = null; render();
  const d = await api("/api/shift/open", { seed: S.seed, alert_id: a.id });
  S.detail = d.error ? null : d; render();
}

function decide(x) { const a = S.data.alerts[S.sel]; if (S.opened.includes(a.id)) { S.decided[a.id] = x; render(); } }

async function finish() {
  if (S.over) return; S.over = true; clearInterval(S.timer);
  const escd = Object.entries(S.decided).filter(([, v]) => v === "escalate").map(([k]) => k);
  const r = await api("/api/shift/score", { seed: S.seed, opened: S.opened, escalated: escd });
  const byId = Object.fromEntries(S.data.alerts.map((a) => [a.id, a]));
  const row = (label, s) => `<tr><td data-label="">${label}</td><td class="n" data-label="Laundering caught">${fmt(s.caught_micros)}</td><td class="n" data-label="False alarms">${s.false_alarms}</td><td class="n" data-label="Money recovered">${fmt(s.recovered_micros)}</td><td class="n" data-label="Score"><strong>${fmt(s.score_micros)}</strong></td></tr>`;
  const yours = S.opened.map((id) => { const t = r.truth[id], a = byId[id], d = S.decided[id] || "opened, not decided (counts as cleared)";
    const right = (t.laundering && d === "escalate") || (!t.laundering && d !== "escalate");
    return `<tr><td data-label="Alert">${esc(a.rule)}</td><td data-label="You">${d}</td><td data-label="Truth">${t.laundering ? `laundering (${esc(t.patterns.join(", "))})` : "benign"}</td><td data-label="Right?">${right ? "✓ right" : "✗ wrong"}</td></tr>`; }).join("");
  main.innerHTML = `<section class="card" style="margin:24px 0">
    <p class="eyebrow">End of shift · seed ${esc(String(r.truth ? S.data.seed : ""))}</p>
    <h1>You caught ${fmt(r.you.caught_micros)} of laundering.</h1>
    <div class="tablewrap"><table class="t stack"><thead><tr><th>With ${S.data.budget} reviews</th><th class="n">Laundering caught</th><th class="n">False alarms</th><th class="n">Money recovered</th><th class="n">Score</th></tr></thead>
      <tbody>${row("You", r.you)}${row("AgentGuard's ranked queue (severity, then amount)", r.engine_ranked)}${row("Best possible picks", r.best)}</tbody></table></div>
    <p class="hint">${esc(r.penalty_note)} Money recovered = later laundering payments by the same agents, stopped because escalation holds the agent.</p>
    <p><strong>Laundering in alerts you didn't open:</strong> ${fmt(r.you.missed_in_queue_micros)} · <strong>Laundering no rule alerted on</strong> (mostly a slow drip kept under the structuring band): ${fmt(r.you.never_alerted_micros)}</p>
    <div class="why approved"><p><strong>The lesson from the IBM benchmark:</strong> with a limited review budget, ranking matters more than catching everything. On IBM HI-Small, AgentGuard's ranked rules found about ten times more laundering than an amount threshold at 50 reviews a day.</p></div>
    <h3 style="margin-top:16px">Your reviews</h3><div class="tablewrap"><table class="t stack"><thead><tr><th>Alert</th><th>You</th><th>Truth</th><th></th></tr></thead><tbody>${yours || '<tr><td colspan="4">You opened no alerts.</td></tr>'}</tbody></table></div>
    <div class="actions" style="margin-top:16px"><button class="btn btn-p" id="again">Play a practice shift</button><a class="btn btn-s" href="/pro#ibm">See the IBM results</a></div></section>`;
  document.getElementById("again").onclick = () => { intro(); };
}

addEventListener("keydown", (e) => {
  if (!S.data || S.over || e.target.matches("input, textarea")) return;
  const k = e.key.toLowerCase();
  if (k === "j") { S.sel = Math.min(S.data.alerts.length - 1, S.sel + 1); render(); }
  else if (k === "k") { S.sel = Math.max(0, S.sel - 1); render(); }
  else if (k === "enter") openSel();
  else if (k === "e") decide("escalate");
  else if (k === "c") decide("clear");
});
intro();
