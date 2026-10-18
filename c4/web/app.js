"use strict";

/* ---------- small helpers ---------- */
const $ = (selector) => document.querySelector(selector);

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

async function api(path, body) {
  const options = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    throw new Error("Cannot reach the C4 server. Is scripts/run_c4_server.py running?");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

/* ---------- state ---------- */
const state = { meta: null, target: null, preset: null, learner: null, report: null, ollamaReady: false };

const targetInfo = () => state.meta.targets.find((item) => item.id === state.target);

function setChip(id, ok, label) {
  const chip = $(id);
  chip.dataset.state = ok ? "ok" : "off";
  if (label) chip.lastChild.textContent = label;
}

function showError(message) {
  const box = $("#error");
  box.hidden = !message;
  box.textContent = message || "";
}

/* ---------- inputs ---------- */
const PRESET_LABELS = {
  demo_learner: "Demo learner (L02, from fixture)",
  all_mastered: "All prerequisites mastered",
  missing_prereq: "One prerequisite missing",
  several_low: "Several low-mastery concepts",
  uncertain: "Mastery estimates uncertain",
};

function renderLearnerSummary() {
  const box = $("#learner-summary");
  box.replaceChildren();
  const learner = state.learner;
  const target = targetInfo();
  const shown = new Set([...target.prerequisites]);
  Object.keys(learner.mastery).forEach((id) => { if (id !== target.id) shown.add(id); });
  for (const id of shown) {
    const mastery = learner.mastery[id];
    const text = mastery === undefined ? "no data" : mastery.toFixed(2);
    box.append(el("span", { class: "chip" }, state.meta.concepts[id] || id, " · ", text));
  }
}

function learnerConcepts() {
  const target = targetInfo();
  const ordered = [...target.prerequisites, ...Object.keys(state.meta.concepts)];
  return [...new Set(ordered)].filter((id) => id !== target.id);
}

function markCustom() {
  const select = $("#preset");
  if (!select.querySelector('option[value="custom"]')) select.append(el("option", { value: "custom" }, "Custom (edited)"));
  select.value = "custom";
  state.preset = "custom";
  renderLearnerSummary();
}

function renderLearnerEditor() {
  const box = $("#learner-editor");
  box.replaceChildren();
  for (const id of learnerConcepts()) {
    const has = state.learner.mastery[id] !== undefined;
    const mastery = state.learner.mastery[id] ?? 0.5;
    const spread = state.learner.uncertainty[id] ?? 0.2;
    const row = el("div", { class: "lrow", "data-off": String(!has) });
    const sync = () => {
      const on = check.checked;
      row.dataset.off = String(!on);
      if (on) {
        state.learner.mastery[id] = Number(m.value);
        state.learner.uncertainty[id] = Number(u.value);
      } else {
        delete state.learner.mastery[id];
        delete state.learner.uncertainty[id];
      }
      mv.textContent = Number(m.value).toFixed(2);
      uv.textContent = Number(u.value).toFixed(2);
      markCustom();
    };
    const check = el("input", { type: "checkbox", "aria-label": `Has history for ${state.meta.concepts[id]}`, onchange: sync });
    check.checked = has;
    const m = el("input", { type: "range", min: 0, max: 1, step: 0.05, value: mastery, "aria-label": "mastery", oninput: sync });
    const u = el("input", { type: "range", min: 0, max: 1, step: 0.05, value: spread, "aria-label": "uncertainty", oninput: sync });
    const mv = el("span", {}, Number(mastery).toFixed(2));
    const uv = el("span", {}, Number(spread).toFixed(2));
    row.append(check, el("span", { class: "lname" }, state.meta.concepts[id] || id),
      el("div", { class: "lsliders" }, "mastery", m, mv), el("div", { class: "lsliders" }, "uncertainty", u, uv));
    box.append(row);
  }
}

function applyPreset() {
  if ($("#preset").value === "custom") return;  // edited learner stays as typed
  state.preset = $("#preset").value;
  state.learner = JSON.parse(JSON.stringify(targetInfo().learner_presets[state.preset]));
  renderLearnerSummary();
  renderLearnerEditor();
}

function applyTarget() {
  state.target = $("#target").value;
  $('#preset option[value="custom"]')?.remove();
  if ($("#preset").value === "custom" || !$("#preset").value) $("#preset").value = "demo_learner";
  const target = targetInfo();
  const names = target.prerequisites.map((id) => state.meta.concepts[id] || id);
  $("#path-hint").textContent = names.length
    ? `Prerequisites in the graph: ${names.join(", ")}.`
    : "No prerequisites in the graph.";
  applyPreset();
  $("#explanation").value = target.scenarios.mixed;
  updateCount();
}

function updateCount() {
  $("#char-count").textContent = `${$("#explanation").value.length} / 2000`;
}

/* ---------- verifier settings ---------- */
function readConfig() {
  return {
    check_factual: $("#cfg-factual").checked,
    check_cognitive: $("#cfg-cognitive").checked,
    rewrite: $("#cfg-rewrite").checked,
    max_rewrite_attempts: Number($("#cfg-attempts").value),
    mastery_threshold: Number($("#cfg-mastery").value),
    uncertainty_threshold: Number($("#cfg-uncertainty").value),
  };
}

function syncConfigLabels() {
  $("#cfg-attempts-val").textContent = $("#cfg-attempts").value;
  $("#cfg-mastery-val").textContent = Number($("#cfg-mastery").value).toFixed(2);
  $("#cfg-uncertainty-val").textContent = Number($("#cfg-uncertainty").value).toFixed(2);
}

function resetConfig() {
  const d = state.meta.config_defaults;
  $("#cfg-factual").checked = d.check_factual;
  $("#cfg-cognitive").checked = d.check_cognitive;
  $("#cfg-rewrite").checked = d.rewrite;
  $("#cfg-attempts").value = d.max_rewrite_attempts;
  $("#cfg-mastery").value = d.mastery_threshold;
  $("#cfg-uncertainty").value = d.uncertainty_threshold;
  syncConfigLabels();
}

/* ---------- examples and generators ---------- */
function loadScenario(name) {
  $("#explanation").value = targetInfo().scenarios[name];
  $("#prompt-box").hidden = true;
  updateCount();
}

async function generate(source) {
  showError("");
  const buttons = [$("#gen-template"), $("#gen-ollama")];
  const label = $(source === "ollama" ? "#gen-ollama" : "#gen-template");
  const original = label.textContent;
  buttons.forEach((b) => { b.disabled = true; });
  label.textContent = source === "ollama" ? "Writing… (a few seconds)" : "Writing…";
  try {
    const result = await api("/api/generate", { target: state.target, source, learner: state.learner });
    $("#explanation").value = result.explanation;
    updateCount();
    $("#prompt-box").hidden = !result.prompt;
    $("#prompt-text").textContent = result.prompt || "";
  } catch (error) {
    showError(error.message);
  } finally {
    label.textContent = original;
    buttons.forEach((b) => { b.disabled = false; });
    $("#gen-ollama").disabled = !state.ollamaReady;
  }
}

/* ---------- run ---------- */
async function run() {
  showError("");
  const button = $("#run");
  button.disabled = true;
  button.textContent = "Verifying…";
  try {
    state.report = await api("/api/verify", {
      target: state.target,
      explanation: $("#explanation").value,
      learner: state.learner,
      config: readConfig(),
    });
    renderReport(state.report);
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Verify and repair";
  }
}

/* ---------- result rendering ---------- */
const FACTUAL_TONE = { ENTAILED: "ok", CONTRADICTED: "bad", UNSUPPORTED: "warn" };
const COGNITIVE_TONE = {
  APPROPRIATE: "ok", BLOOM_MISMATCH: "bad", UNMASTERED_PREREQUISITE: "bad", INCONCLUSIVE: "warn",
};
const CONFIDENCE_TONE = { HIGH: "ok", MEDIUM: "info", LOW: "warn" };
const VIOLATION_HELP = {
  CONTRADICTED_CLAIM: "The knowledge graph states the opposite (or the claim negates a graph fact).",
  UNSUPPORTED_CLAIM: "No graph statement supports this claim, so it cannot be treated as verified.",
  BLOOM_MISMATCH: "The claim asks for a higher cognitive level than this learner's current Bloom ceiling.",
  UNMASTERED_PREREQUISITE: "The claim relies on a concept the learner has not yet mastered.",
  INCONCLUSIVE_COGNITIVE: "Learner evidence is missing, uncertain, or too close to the threshold to decide.",
};
const pretty = (text) => text.replaceAll("_", " ").toLowerCase();

function badge(tone, key, value) {
  return el("span", { class: `badge ${tone}` }, key ? el("span", { class: "k" }, key) : null, value);
}

function pct(value) {
  return value === null || value === undefined ? "n/a" : `${value}%`;
}

function tile(label, value, sub, good) {
  return el("div", { class: `tile${good ? " good" : ""}` },
    el("div", { class: "label" }, label), el("div", { class: "value" }, value),
    sub ? el("div", { class: "sub" }, sub) : null);
}

function change(before, after) {
  return el("span", {}, pct(before), el("span", { class: "arrow" }, "→"), pct(after));
}

function claimCard(claim) {
  const names = claim.concept_ids.map((id) => state.meta.concepts[id] || id);
  const why = claim.violations.map((v) => VIOLATION_HELP[v]).filter(Boolean);
  return el("article", { class: "claim", "data-ok": String(claim.accepted) },
    el("div", { class: "claim-head" },
      el("span", { class: "claim-id" }, claim.claim_id),
      badge(CONFIDENCE_TONE[claim.confidence], "confidence", claim.confidence.toLowerCase())),
    el("p", { class: "claim-text" }, claim.text),
    el("div", { class: "badges" },
      badge(FACTUAL_TONE[claim.factual_status], "factual", pretty(claim.factual_status)),
      badge(COGNITIVE_TONE[claim.cognitive_status], "cognitive", pretty(claim.cognitive_status)),
      badge("", "Bloom ≈", claim.estimated_bloom_level),
      names.map((name) => badge("info", "", name)),
      claim.violations.map((v) => badge("bad", "", pretty(v)))),
    claim.evidence.length
      ? el("div", { class: "evidence" }, el("b", {}, "Graph evidence: "), claim.evidence.join(" · "))
      : el("div", { class: "evidence" }, el("b", {}, "Graph evidence: "), "none found"),
    why.map((line) => el("div", { class: "why" }, line)));
}

function block(title, lede, content) {
  return el("section", { class: "block" }, el("h3", {}, title),
    lede ? el("p", { class: "lede" }, lede) : null, content);
}

function renderReport(report) {
  const m = report.metrics;
  const clean = report.unresolved_claims.length === 0;
  const tiles = el("div", { class: "tiles" },
    tile("Bloom ceiling", report.bloom_ceiling, "highest level allowed for this learner"),
    tile("Hallucination rate", change(m.before.hallucination_rate, m.after.hallucination_rate),
      "claims not supported by the graph", m.after.hallucination_rate === 0),
    tile("Cognitive mismatch", change(m.before.cognitive_mismatch_rate, m.after.cognitive_mismatch_rate),
      "claims unsuitable for the learner", m.after.cognitive_mismatch_rate === 0),
    tile("Rewrite success", pct(m.rewrite_success_rate),
      `${m.claims_corrected} of ${m.claims_sent_for_rewrite} flagged claims fixed`,
      m.rewrite_success_rate === 100),
    tile("New violations", m.new_violations_introduced, "introduced by rewriting", m.new_violations_introduced === 0),
    tile("Latency", `${(report.latency_s * 1000).toFixed(1)} ms`, "verifier only, no LLM calls"));

  const trace = report.rewrite_trace.length
    ? el("div", { class: "trace" }, report.rewrite_trace.map((step) =>
        el("div", { class: "step" },
          el("div", { class: "step-head" }, el("b", {}, `Round ${step.attempt} · ${step.claim_id}`),
            step.violations.map((v) => badge("bad", "", pretty(v))), badge("info", "via", step.strategy)),
          el("div", { class: "diff" },
            el("p", { class: "del" }, step.before),
            el("p", { class: "add" }, step.after || "(sentence removed — its content is already stated)")))))
    : el("p", { class: "lede" }, "No claim violated a rule, so nothing was rewritten.");

  const notice = el("div", { class: "notice" },
    clean ? badge("ok", "", "all claims verified")
          : badge("warn", "", `unresolved: ${report.unresolved_claims.join(", ")} — not presented as verified`),
    report.review_first.length ? el("span", {}, "Review first:") : null,
    report.review_first.map((id) => badge("info", "", state.meta.concepts[id] || id)));

  const json = JSON.stringify(report, null, 2);
  const details = el("details", { class: "json" }, el("summary", {}, "Faithfulness report (JSON, schema c4-report/1.0)"),
    el("pre", {}, json),
    el("div", { class: "json-actions" }, el("button", { type: "button", onclick: () => downloadJson(json) }, "Download JSON")));

  $("#results").replaceChildren(
    tiles,
    block("Initial verification", "Every sentence is one claim, labelled on two independent dimensions.",
      el("div", { class: "claims" }, report.initial_claims.map(claimCard))),
    block("Targeted rewrites", "Only violating claims are changed; valid claims are left exactly as written.", trace),
    block("Re-verification", "Rewritten text passes through the same checks before it is accepted.",
      el("div", { class: "claims" }, report.claims.map(claimCard))),
    block("Final explanation", null,
      el("div", { class: `final${clean ? "" : " unresolved"}` }, report.final_explanation || "(empty)")),
    notice, details);

  const stages = { decompose: true, verify: true, rewrite: report.rewrite_trace.length > 0,
    reverify: report.rewrite_trace.length > 0, report: true };
  document.querySelectorAll("#pipeline li").forEach((item) =>
    item.classList.toggle("done", stages[item.dataset.stage]));
}

function downloadJson(text) {
  const link = el("a", { href: URL.createObjectURL(new Blob([text], { type: "application/json" })),
    download: `c4-report-${state.target}.json` });
  document.body.append(link);
  link.click();
  link.remove();
}

/* ---------- tabs and boot ---------- */
function selectTab(name) {
  for (const id of ["verify", "eval"]) {
    $(`#tab-${id}`).setAttribute("aria-selected", String(id === name));
    $(`#view-${id}`).hidden = id !== name;
  }
}

async function boot() {
  $("#tab-verify").addEventListener("click", () => selectTab("verify"));
  $("#tab-eval").addEventListener("click", () => selectTab("eval"));
  $("#target").addEventListener("change", applyTarget);
  $("#preset").addEventListener("change", applyPreset);
  $("#explanation").addEventListener("input", updateCount);
  $("#run").addEventListener("click", run);
  $("#reset").addEventListener("click", () => { applyTarget(); resetConfig(); showError(""); });
  document.querySelectorAll("[data-scenario]").forEach((b) =>
    b.addEventListener("click", () => loadScenario(b.dataset.scenario)));
  $("#gen-template").addEventListener("click", () => generate("template"));
  $("#gen-ollama").addEventListener("click", () => generate("ollama"));
  ["#cfg-attempts", "#cfg-mastery", "#cfg-uncertainty"].forEach((id) => $(id).addEventListener("input", syncConfigLabels));
  $("#gen-ollama").disabled = true;
  try {
    state.meta = await api("/api/meta");
    setChip("#chip-api", true);
  } catch (error) {
    setChip("#chip-api", false);
    showError(error.message);
    return;
  }
  $("#target").replaceChildren(...state.meta.targets.map((item) => el("option", { value: item.id }, item.name)));
  $("#target").value = "heap";
  const presets = Object.keys(state.meta.targets[0].learner_presets);
  $("#preset").replaceChildren(...presets.map((id) => el("option", { value: id }, PRESET_LABELS[id] || id)));
  applyTarget();
  resetConfig();
  if (location.hash === "#run") run();  // deep link used for demos and screenshots
  api("/api/health").then((health) => {
    const { online, model_installed: installed, model } = health.ollama;
    state.ollamaReady = online && installed;
    $("#gen-ollama").disabled = !state.ollamaReady;
    $("#gen-ollama").title = state.ollamaReady ? "Generate a draft with the local model" : "Start Ollama and install qwen3:4b to enable";
    setChip("#chip-ollama", state.ollamaReady, online ? (installed ? model : `${model} missing`) : "Ollama offline");
  }).catch(() => setChip("#chip-ollama", false, "Ollama offline"));
}

boot();
