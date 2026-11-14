// Shared helpers. Every number shown comes from the API, which comes from the engine.
export const fmt = (micros) => {
  const v = Math.round(Number(micros || 0) / 10000) / 100;
  return (v < 0 ? "−$" : "$") + Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, { credentials: "same-origin", ...opt });
  let data = {};
  try { data = await r.json(); } catch { data = { error: "The server sent an unexpected reply." }; }
  if (!r.ok && !data.error) data.error = `Request failed (${r.status}).`;
  return data;
}
const ICON = {
  approved: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M5 12l5 5L19 7"/></svg>',
  held: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  blocked: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.6"><circle cx="12" cy="12" r="9"/><path d="M6 6l12 12"/></svg>',
};
export const verdictOf = (outcome) => outcome === "APPROVED" ? "approved" : outcome === "PENDING_APPROVAL" ? "held" : "blocked";
export const WORD = { approved: "Approved", held: "Held", blocked: "Blocked" };
export const stamp = (v, sm = false) => `<span class="stamp ${v}${sm ? " sm" : ""}" role="img" aria-label="Verdict: ${WORD[v]}">${ICON[v]}${WORD[v]}</span>`;
export const short = (h) => (h || "").slice(0, 12) + "…";
export function setTotals(v) {
  const p = document.getElementById("tot-protected"), l = document.getElementById("tot-lost");
  if (p) { p.textContent = fmt(v.protected); p.classList.remove("tick"); void p.offsetWidth; p.classList.add("tick"); }
  if (l) l.textContent = fmt(v.lost);
}
