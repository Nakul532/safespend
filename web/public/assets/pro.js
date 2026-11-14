import { esc } from "/assets/common.js";

const usd = (s) => "$" + Number(s).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pct = (x, d = 1) => x == null ? "—" : (100 * x).toFixed(d) + "%";
const COLORS = ["#C9C3B6", "#8A93A3", "#6D7ACF", "#3D4FC9", "#0E7C5A", "#151A22"];

function bars(e1) {
  // Attacks stopped per set, one bar per configuration, every bar labelled with its value.
  const W = 760, bh = 13, gap = 4, pad = 210, n = e1[0].cells.length, groupH = n * (bh + gap) + 26;
  const H = e1.length * groupH + 10, maxW = W - pad - 70;
  let y = 8, g = "";
  for (const row of e1) {
    g += `<text class="lab" x="0" y="${y + 12}">${esc(row.set.replace(/ \(.*\)$/, ""))}</text>`;
    row.cells.forEach((c, i) => {
      const v = c.attacks ? c.stopped / c.attacks : 0, w = Math.max(2, maxW * v), yy = y + i * (bh + gap);
      g += `<text x="${pad - 8}" y="${yy + bh - 2}" text-anchor="end">${esc(c.config.split(" ")[0])}</text>`;
      g += `<rect x="${pad}" y="${yy}" width="${w}" height="${bh}" rx="2" fill="${COLORS[i]}"><title>${esc(c.config)}: ${c.stopped}/${c.attacks}</title></rect>`;
      g += `<text x="${pad + w + 6}" y="${yy + bh - 2}">${c.stopped}/${c.attacks}</text>`;
    });
    y += groupH;
  }
  const legend = `<div class="legend" style="margin-bottom:8px">${e1[0].cells.map((c, i) => `<span><i style="background:${COLORS[i]}"></i><strong>${esc(c.config.split(" ")[0])}</strong> ${esc(c.config.split(" ").slice(1).join(" "))}</span>`).join("")}</div>`;
  return legend + `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="Attacks stopped by configuration, per set">${g}</svg>`;
}

function e1(d) {
  const head = `<tr><th>Set</th>${d.configs.map((c) => `<th>${esc(c)}</th>`).join("")}</tr>`;
  const body = d.e1.map((r) => `<tr><td>${esc(r.set)}</td>${r.cells.map((c) => `<td class="cell"><b>${c.stopped}/${c.attacks}</b>
    <small>${usd(c.lost)} lost</small><small>${c.legit ? `${c.false_blocks}/${c.legit} false blocks` : "no legit tasks"} · ${c.held_pct}% held</small></td>`).join("")}</tr>`).join("");
  return `<h2>Red-team results (E1)</h2><p>Attacks stopped, simulated dollars lost, legitimate tasks blocked and the share of payments held for a human, for each locked set. Each configuration adds one layer. Everything from C2 on includes parts <strong>added after the suites were locked</strong>; C1 is the "before".</p>
    ${bars(d.e1)}<div class="tablewrap" style="margin-top:16px"><table class="t">${head}${body}</table></div>
    <p class="small muted">Owner incidents under C0: two scenarios have a $0 attack amount, which counts as stopped with no guardrails. The three LLM runs gave identical results. Under C5, 6 of 55 legitimate v1 tasks are held for a human (5 by the commitment hold on subscription renewals); none are blocked.</p>`;
}

function e2(d) {
  const b = d.e2.budgets, ks = Object.keys(b);
  const W = 640, H = 220, x0 = 50, y0 = 190, maxY = Math.max(...ks.map((k) => b[k].rules.recall)) * 1.15;
  const X = (i) => x0 + 10 + i * ((W - x0 - 70) / (ks.length - 1)), Y = (v) => y0 - (v / maxY) * 170;
  const line = (key, col) => `<polyline fill="none" stroke="${col}" stroke-width="3" points="${ks.map((k, i) => `${X(i)},${Y(b[k][key].recall)}`).join(" ")}"/>` +
    ks.map((k, i) => `<circle cx="${X(i)}" cy="${Y(b[k][key].recall)}" r="4" fill="${col}"/>`).join("");
  const ticks = [0, maxY / 2, maxY].map((v) => `<text x="4" y="${Y(v) + 4}">${(100 * v).toFixed(0)}%</text><line x1="${x0}" x2="${W - 20}" y1="${Y(v)}" y2="${Y(v)}" stroke="#E3DED3"/>`).join("");
  const chart = `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="Recall at daily alert budgets">${ticks}
    <line x1="${x0}" y1="${y0}" x2="${W - 10}" y2="${y0}" stroke="#E3DED3"/>${ks.map((k, i) => `<text x="${X(i) - 14}" y="${y0 + 18}">${k.split("/")[0].slice(2)}/day</text>`).join("")}
    ${line("rules", "#3D4FC9")}${line("baseline_top_amounts", "#B33A2E")}<text x="${x0}" y="10">recall (share of laundering caught)</text></svg>
    <div class="legend"><span><i style="background:#3D4FC9"></i>AgentGuard rules, ranked</span><span><i style="background:#B33A2E"></i>Baseline: largest transfers</span></div>`;
  const rows = ks.map((k) => `<tr><td>${k.split("/")[0].slice(2)}</td><td class="n">${pct(b[k].rules.recall)}</td><td class="n">${pct(b[k].rules.alert_precision)}</td><td class="n">${pct(b[k].baseline_top_amounts.recall)}</td></tr>`).join("");
  const u = d.e2.unbudgeted;
  const pats = Object.entries(d.e2.recall_by_pattern).map(([p, v]) => `<tr><td>${esc(p)}</td><td class="n">${v.laundering_txns.toLocaleString()}</td><td class="n">${pct(v.rules_recall)}</td><td class="n">${pct(v.baseline_recall)}</td></tr>`).join("");
  return `<h2 id="ibm">IBM AML benchmark (E2) <span class="src">BENCHMARK</span></h2>
    <p>IBM HI-Small, ${esc(d.e2.subset)}: ${d.e2.transactions.toLocaleString()} synthetic bank transfers, ${d.e2.laundering.toLocaleString()} labelled laundering. The rules were written for agents paying merchants; here they run on bank accounts with settings fixed before reading labels.</p>
    <p><strong>All alerts, no budget:</strong> rules precision ${pct(u.rules.precision, 2)}, recall ${pct(u.rules.recall)}; a $10,000 threshold: precision ${pct(u.baseline.precision, 2)}, recall ${pct(u.baseline.recall)}. Without a budget the rules are no better than the threshold.</p>
    <h3>When analysts can review K alerts a day</h3>${chart}
    <div class="tablewrap"><table class="t"><tr><th>K per day</th><th class="n">Rules: recall</th><th class="n">Rules: alerts with laundering</th><th class="n">Baseline: recall</th></tr>${rows}</table></div>
    <h3>Rapid-fire retune (added after Stage 3)</h3><p>Tuned on days 1–3 only, tested once on days 4–7: alerts ${d.rapidfire.before.alerts.toLocaleString()} → ${d.rapidfire.after.alerts.toLocaleString()}, false-positive rate ${pct(d.rapidfire.before.fpr)} → ${pct(d.rapidfire.after.fpr)}, recall ${pct(d.rapidfire.before.recall)} → ${pct(d.rapidfire.after.recall)}.</p>
    <h3>Recall by laundering pattern</h3><div class="tablewrap"><table class="t"><tr><th>Pattern</th><th class="n">Laundering txns</th><th class="n">Rules</th><th class="n">Baseline</th></tr>${pats}</table></div>
    <p class="small muted">The rules miss chain patterns (stack, cycle, bipartite) that need graph analysis.</p>`;
}

function latency(d) {
  const l = d.latency;
  return `<h2>Latency <span class="src">MEASURED</span></h2><div class="tablewrap"><table class="t"><tr><th>Path</th><th class="n">p50</th><th class="n">p95</th></tr>
    <tr><td>Deterministic policy decision (no LLM)</td><td class="n">${l.deterministic_path_ms.p50} ms</td><td class="n">${l.deterministic_path_ms.p95} ms</td></tr>
    <tr><td>LLM check (Groq API, gpt-oss-120b)</td><td class="n">${Math.round(l.llm_api_ms.p50)} ms</td><td class="n">${Math.round(l.llm_api_ms.p95)} ms</td></tr></table></div>
    <p>Payments that needed the LLM: ${l.share_needing_llm.llm_steps} of ${l.share_needing_llm.all_steps} (${l.share_needing_llm.pct}%) across the red-team sets, which are heavy in injection scenarios. The LLM runs only when the agent read outside content or the payment is near a limit.</p>`;
}

function lookalike(d) {
  const a = d.lookalike.test_a_vs_world_merchants, b = d.lookalike.test_b_vs_top_registrants;
  return `<h2>Look-alike false positives</h2><p>Real, distinct companies from the SEC's public <code>company_tickers.json</code>, so every flag is a false positive.</p>
    <div class="tablewrap"><table class="t"><tr><th>Trusted list</th><th class="n">Names checked</th><th class="n">Flagged</th><th class="n">Rate</th></tr>
    <tr><td>The suite's 9 fictional merchants</td><td class="n">${a.checked.toLocaleString()}</td><td class="n">${a.flagged}</td><td class="n">${a.pct}%</td></tr>
    <tr><td>The 500 largest SEC registrants</td><td class="n">${b.checked.toLocaleString()}</td><td class="n">${b.flagged}</td><td class="n">${b.pct}%</td></tr></table></div>
    <p>Examples: ${b.examples.slice(0, 8).map((e) => `${esc(e[0])} → ${esc(e[1])}`).join("; ")}.</p>
    <p>With 50 or more trusted merchants a match now holds for a human (LOOKALIKE_REVIEW) instead of blocking, so none of these companies would be blocked.</p>`;
}

function newer(d) {
  const r = d.intent.run1.totals, e = d.e3, t = e.totals, v = e.judge_verdicts_on_kept_sentences;
  const kept = t.kept_sentences;
  return `<h2>Intent check <span class="tag-after">added after lock</span></h2>
    <p>26 locked cases written by a fresh agent before the check existed. Three runs, identical: <strong>${r.mismatch_held}/${r.mismatch_total}</strong> mismatches held, <strong>${r.match_allowed}/${r.match_total}</strong> matches allowed. Field checks alone (limit, category, cash equivalents) catch ${r.held_by_fields} of ${r.mismatch_total}; the model adds the rest. The set is small and written by the builder's model family, so treat the perfect score with caution.</p>
    <h2>AI investigator case notes (E3)</h2>
    <p>30 alerts from synthetic agent data. The investigator (${esc(e.investigator_model)}) cited ${t.cited_total} transaction IDs; <strong>${(100 * e.citation_existence_rate).toFixed(0)}%</strong> exist and were in the evidence it was shown. Code dropped ${t.raw_sentences - kept} of ${t.raw_sentences} sentences for containing numbers (digits or spelled out), so no model-written number is ever displayed.</p>
    <p>An independent judge (${esc(e.judge_model)}, a different model family) rated the ${kept} kept sentences: ${v.supported} supported (${Math.round(100 * v.supported / kept)}%), ${v.partly} partly, ${v.unsupported} unsupported (${Math.round(100 * v.unsupported / kept)}%). Typical failure: claiming context it wasn't shown, such as "just under the threshold" for a payment far below it. Ten notes are set aside for human hand-scoring.</p>`;
}

const TABS = [["results", "Red-team results", e1], ["ibm", "IBM benchmark", e2], ["latency", "Latency", latency],
  ["lookalike", "Look-alike false positives", lookalike], ["newer", "Intent check and case notes", newer],
  ["validation", "Model validation report", (d) => d.docs.validation], ["controls", "Control matrix", (d) => d.docs.controls]];

fetch("/data/pro.json").then((r) => r.json()).then((d) => {
  const want = (location.hash || "#results").slice(1);
  const on = TABS.some((t) => t[0] === want) ? want : "results";
  document.getElementById("tabs").innerHTML = TABS.map(([k, label]) => `<button class="tab" role="tab" aria-selected="${k === on}" data-k="${k}">${label}</button>`).join("");
  document.getElementById("sections").innerHTML = TABS.map(([k, , f]) => `<section id="s-${k}" class="${k === on ? "on" : ""}" role="tabpanel">${f(d)}</section>`).join("");
  const show = (k) => {
    document.querySelectorAll("[data-k]").forEach((x) => x.setAttribute("aria-selected", x.dataset.k === k));
    document.querySelectorAll(".doc section").forEach((s) => s.classList.toggle("on", s.id === "s-" + k));
  };
  document.querySelectorAll("[data-k]").forEach((b) => b.onclick = () => { show(b.dataset.k); history.replaceState(null, "", "#" + b.dataset.k); });
  addEventListener("hashchange", () => { const k = location.hash.slice(1); if (TABS.some((t) => t[0] === k)) show(k); });
});
