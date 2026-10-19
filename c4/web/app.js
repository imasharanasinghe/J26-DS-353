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
const state = { meta: null, target: null, preset: null, learner: null, report: null, ollamaReady: false, journey: null };

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
  refreshInputsView();
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
  state.journey = freshJourney();
  refreshProgressionView();
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

function refreshInputsView() {
  if (!$("#view-inputs").hidden) renderInputs();
}

function updateCount() {
  $("#char-count").textContent = `${$("#explanation").value.length} / 20000`;
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
    const result = await api("/api/generate", { target: state.target, source, learner: state.learner, config: readConfig() });
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
async function run(source = null) {
  showError("");
  const button = $("#run");
  const auto = [$("#auto-template"), $("#auto-ollama")];
  button.disabled = true;
  auto.forEach((b) => { b.disabled = true; });
  button.textContent = source ? "Drafting and verifying…" : "Verifying…";
  $("#results").setAttribute("aria-busy", "true");
  try {
    const body = { target: state.target, learner: state.learner, config: readConfig() };
    if (source) {
      state.report = await api("/api/explain", { ...body, source });
      $("#explanation").value = state.report.original_explanation;
      updateCount();
      $("#prompt-box").hidden = !state.report.prompt;
      $("#prompt-text").textContent = state.report.prompt || "";
    } else {
      state.report = await api("/api/verify", { ...body, explanation: $("#explanation").value });
    }
    renderReport(state.report);
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    auto.forEach((b) => { b.disabled = false; });
    $("#auto-ollama").disabled = !state.ollamaReady;
    button.textContent = "Verify and repair";
    $("#results").removeAttribute("aria-busy");
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

const LABEL_HELP = {
  ENTAILED: "A graph statement supports this claim.",
  CONTRADICTED: "The graph states the opposite.",
  UNSUPPORTED: "No graph statement supports this claim.",
  APPROPRIATE: "Suitable for this learner at this point.",
  BLOOM_MISMATCH: "Asks for a higher cognitive level than the learner's Bloom ceiling.",
  UNMASTERED_PREREQUISITE: "Relies on a concept the learner has not mastered.",
  INCONCLUSIVE: "Learner evidence is missing, uncertain, or too close to the threshold.",
};

function badge(tone, key, value, help) {
  return el("span", { class: `badge ${tone}`, title: help || null },
    key ? el("span", { class: "k" }, key) : null, value);
}

function pct(value) {
  if (value === null || value === undefined) return "n/a";
  const n = Number(value);
  return `${Number.isInteger(n) ? n : n.toFixed(1)}%`;
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
      badge(FACTUAL_TONE[claim.factual_status], "factual", pretty(claim.factual_status), LABEL_HELP[claim.factual_status]),
      badge(COGNITIVE_TONE[claim.cognitive_status], "cognitive", pretty(claim.cognitive_status), LABEL_HELP[claim.cognitive_status]),
      badge("", "Bloom ≈", claim.estimated_bloom_level, "Estimated cognitive level of the sentence (1 remember … 6 create)."),
      names.map((name) => badge("info", "", name)),
      claim.violations.map((v) => badge("bad", "", pretty(v), VIOLATION_HELP[v]))),
    claim.evidence.length
      ? el("div", { class: "evidence" }, el("b", {}, "Graph evidence: "), claim.evidence.join(" · "))
      : el("div", { class: "evidence" }, el("b", {}, "Graph evidence: "), "none found"),
    why.map((line) => el("div", { class: "why" }, line)));
}

function block(title, lede, content) {
  return el("section", { class: "block" }, el("h3", {}, title),
    lede ? el("p", { class: "lede" }, lede) : null, content);
}

function verdict(report) {
  const initial = report.initial_claims;
  const flagged = initial.filter((c) => !c.accepted);
  const unresolved = report.unresolved_claims.length;
  const kinds = {};
  flagged.forEach((c) => c.violations.forEach((v) => { kinds[v] = (kinds[v] || 0) + 1; }));
  const detail = Object.entries(kinds).map(([v, n]) => `${n} ${pretty(v)}`).join(", ");
  let tone = "ok", title, note;
  if (!flagged.length) {
    title = `All ${initial.length} claim${initial.length === 1 ? "" : "s"} verified`;
    note = "Nothing needed repair; the explanation was left exactly as written.";
  } else if (!unresolved) {
    title = `${flagged.length} of ${initial.length} claims needed repair, and now all pass`;
    note = `Found: ${detail}. Rewritten in ${report.rewrite_attempts} round${report.rewrite_attempts === 1 ? "" : "s"}.`;
  } else {
    tone = "warn";
    title = `${unresolved} claim${unresolved === 1 ? "" : "s"} still not verified`;
    note = `Found: ${detail}. Unresolved claims are not presented as verified.`;
  }
  return el("div", { class: `verdict ${tone}`, role: "status" },
    el("span", { class: "mark", "aria-hidden": "true" }, el("span", {}, tone === "ok" ? "✓" : "!")),
    el("div", {}, el("strong", {}, title), el("small", {}, note)));
}


/* ---------- final explanation document ---------- */
const SVG_NS = "http://www.w3.org/2000/svg";
const ICONS = {
  check: ["M5 12.5l4.5 4.5L19 7.5"],
  rewrite: ["M4 12a8 8 0 0114-5.3L20 9", "M20 4v5h-5", "M20 12a8 8 0 01-14 5.3L4 15", "M4 20v-5h5"],
  alert: ["M12 3.5l9.5 16.5h-19z", "M12 10v4.5", "M12 17.5v.1"],
  info: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 11v5", "M12 8v.1"],
  book: ["M4 4.5h6a2 2 0 012 2V20a2 2 0 00-2-2H4z", "M20 4.5h-6a2 2 0 00-2 2V20a2 2 0 012-2h6z"],
  link: ["M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1", "M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"],
  compass: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M15.5 8.5l-2 5-5 2 2-5z"],
  layers: ["M12 3l9 5-9 5-9-5z", "M3 13l9 5 9-5"],
  question: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M9.6 9.6a2.5 2.5 0 114 2c-1 .8-1.6 1.2-1.6 2.4", "M12 17v.1"],
  target: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 16a4 4 0 100-8 4 4 0 000 8z", "M12 12v.01"],
  flag: ["M5 21V4", "M5 4h11l-2 4 2 4H5"],
  copy: ["M9 9h10v11H9z", "M5 15V4h10"],
};

function icon(name, size = 18) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("width", size);
  svg.setAttribute("height", size);
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  for (const d of ICONS[name] || ICONS.info) {
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

const SECTION_ICONS = [
  [/mistake/i, "alert"], [/before/i, "link"], [/stand/i, "compass"],
  [/refresher/i, "layers"], [/about|what/i, "book"],
];
const sectionIcon = (title) => (SECTION_ICONS.find(([pattern]) => pattern.test(title)) || [null, "info"])[1];

const NODE_STATES = {
  MASTERED: ["ok", "check", "secure"], UNMASTERED: ["bad", "alert", "review"],
  UNKNOWN: ["warn", "question", "check"], TARGET: ["target", "target", "this step"], FIX: ["info", "alert", "fix"],
};

function pathFlow(visual) {
  const flow = el("div", { class: "flow", role: "list", "aria-label": "Verified learning path" });
  visual.nodes.forEach((node, index) => {
    const [tone, glyph, label] = NODE_STATES[node.state] || NODE_STATES.UNKNOWN;
    const detail = node.state === "TARGET" ? label
      : node.state === "FIX" ? label
      : node.mastery === null || node.mastery === undefined ? "no history"
      : `${label} · ${node.mastery.toFixed(2)}`;
    if (index) flow.append(el("span", { class: "arr", "aria-hidden": "true" }, "→"));
    flow.append(el("div", { class: `node ${tone}`, role: "listitem",
      title: node.kind === "probe" ? "Quick check before learning" : null },
      icon(glyph, 17), el("b", {}, node.name.replace(/^Fix: /, "")),
      el("small", {}, node.kind === "probe" ? `check · ${detail}` : detail)));
  });
  const legend = el("div", { class: "legend" },
    ...[["ok", "secure"], ["bad", "review first"], ["warn", "quick check"], ["target", "this step"]]
      .map(([tone, text]) => el("span", {}, el("i", { class: tone }), text)),
    el("span", { class: "ceiling" }, `Bloom ceiling: ${visual.bloom_ceiling_name}`));
  return el("div", { class: "pathbox" }, flow, legend);
}

function finalDocument(report, clean) {
  const layout = report.final_layout;
  if (!layout || !layout.length) {
    return el("div", { class: `final${clean ? "" : " unresolved"}` }, report.final_explanation || "(empty)");
  }
  const claims = new Map(report.claims.map((claim) => [claim.claim_id, claim]));
  const rewritten = report.rewrite_trace.map((step) => step.after).filter(Boolean);
  const sources = [];
  const cite = (evidence) => {
    let index = sources.indexOf(evidence);
    if (index < 0) { sources.push(evidence); index = sources.length - 1; }
    return index + 1;
  };
  const counts = { verified: 0, rewritten: 0, grounded: 0, open: 0 };
  const removed = report.rewrite_trace.filter((step) => !step.after).length;

  const sentence = (id) => {
    const claim = claims.get(id);
    if (!claim) return null;
    const note = claim.evidence[0] || "";
    let kind = "verified", glyph = "check", help = `Verified against the knowledge graph (${claim.confidence.toLowerCase()} confidence).`;
    if (!claim.accepted) { kind = "open"; glyph = "alert"; help = "Not verified: " + claim.violations.map(pretty).join(", "); }
    else if (claim.source === "grounded") { kind = "grounded"; glyph = "info"; help = note; }
    else if (rewritten.some((after) => after.includes(claim.text))) { kind = "rewritten"; glyph = "rewrite"; help = "Rewritten by C4, then re-verified."; }
    counts[kind] += 1;
    const number = kind === "verified" && note ? cite(note) : null;
    return el("span", { class: `sent ${kind}`, title: help },
      el("span", { class: "gut" }, icon(glyph, 14)),
      el("span", { class: "txt" }, claim.text,
        number ? el("sup", { class: "cite", title: note }, `[${number}]`) : null));
  };

  const body = [];
  let list = null;
  for (const line of layout) {
    if (line.kind === "heading") {
      list = null;
      body.push(el(`h${Math.min(4, line.level + 1)}`, { class: `dh dh${line.level}` },
        line.level >= 3 ? el("span", { class: "hi" }, icon(sectionIcon(line.text), 14)) : null, line.text));
    } else if (line.kind === "path") {
      list = null;
      body.push(report.visual ? pathFlow(report.visual) : el("p", { class: "plainpath" }, line.text));
    } else if (line.kind === "bullet") {
      if (!list) { list = el("ul", { class: "dl" }); body.push(list); }
      list.append(el("li", {}, line.claim_ids.map(sentence)));
    } else {
      list = null;
      body.push(el("p", { class: "dp" }, line.claim_ids.map(sentence)));
    }
  }
  const footnotes = sources.length
    ? el("div", { class: "sources" }, el("b", {}, "Graph evidence"),
        el("ol", {}, sources.map((text) => el("li", {}, text))))
    : null;
  const summary = el("div", { class: "docbar" },
    el("div", { class: "stats" },
      el("span", {}, `${counts.verified} verified against the graph`),
      el("span", {}, `${counts.grounded} written from your learner data`),
      counts.rewritten ? el("span", {}, `${counts.rewritten} rewritten`) : null,
      removed ? el("span", {}, `${removed} draft sentence${removed === 1 ? "" : "s"} dropped (covered elsewhere)`) : null,
      counts.open ? el("span", { class: "open" }, `${counts.open} not verified`) : null),
    el("button", { type: "button", class: "ghost copy", onclick: (event) => copyText(report.final_explanation, event.currentTarget) },
      icon("copy", 15), "Copy as Markdown"));
  return el("article", { class: `doc${clean ? "" : " unresolved"}` }, summary, ...body, footnotes);
}

async function copyText(text, button) {
  const label = button.lastChild.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.lastChild.textContent = "Copied";
  } catch (error) {
    button.lastChild.textContent = "Copy not available";
  }
  setTimeout(() => { button.lastChild.textContent = label; }, 1600);
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
            el("p", { class: "add" }, step.after || "(sentence removed — its content is already stated elsewhere)")))))
    : el("p", { class: "lede" }, "No claim violated a rule, so nothing was rewritten.");

  const notice = el("div", { class: "notice" },
    clean ? badge("ok", "", "all claims verified")
          : badge("warn", "", `unresolved: ${report.unresolved_claims.join(", ")} — not presented as verified`),
    report.review_first.length ? el("span", {}, "Review first:") : null,
    report.review_first.map((id) => badge("info", "", state.meta.concepts[id] || id)));

  const json = JSON.stringify(report, null, 2);
  const details = el("details", { class: "json" }, el("summary", {}, "Faithfulness report (JSON, schema c4-report/1.2)"),
    el("pre", {}, json),
    el("div", { class: "json-actions" }, el("button", { type: "button", onclick: () => downloadJson(json) }, "Download JSON")));

  $("#results").replaceChildren(
    verdict(report),
    block("Final explanation", "Every sentence below passed both checks. Hover a sentence for how it was verified.",
      finalDocument(report, clean)),
    tiles,
    block("Initial verification", "Every sentence is one claim, labelled on two independent dimensions.",
      el("div", { class: "claims" }, report.initial_claims.map(claimCard))),
    block("Targeted rewrites", "Only violating claims are changed; valid claims are left exactly as written.", trace),
    block("Re-verification", "Rewritten text passes through the same checks before it is accepted.",
      el("div", { class: "claims" }, report.claims.map(claimCard))),
    notice, details);

  const stages = { decompose: true, verify: true, rewrite: report.rewrite_trace.length > 0,
    reverify: report.rewrite_trace.length > 0, report: true };
  document.querySelectorAll("#pipeline li").forEach((item) =>
    item.classList.toggle("done", stages[item.dataset.stage]));
  if (window.innerWidth <= 920) $("#pipeline").scrollIntoView({ behavior: "smooth", block: "start" });
}

function downloadJson(text) {
  const link = el("a", { href: URL.createObjectURL(new Blob([text], { type: "application/json" })),
    download: `c4-report-${state.target}.json` });
  document.body.append(link);
  link.click();
  link.remove();
}

/* ---------- evaluation tab ---------- */
const CONDITION_LABELS = {
  baseline: "Unverified baseline", factual_only: "Factual-only ablation",
  cognitive_only: "Cognitive-only ablation", full_c4: "Full C4",
};

function barRow(kind, value) {
  const width = Math.max(0, Math.min(100, value ?? 0));
  return el("div", { class: "barrow" },
    el("div", { class: "track", role: "img", "aria-label": `${kind} ${pct(value)}` },
      el("div", { class: `fill ${kind === "Hallucination" ? "fact" : "cog"}`, style: `width:${width}%` })),
    el("span", { class: "num" }, pct(value)));
}

function table(headers, rows, highlight) {
  return el("div", { class: "scroll" }, el("table", { class: "data" },
    el("thead", {}, el("tr", {}, headers.map((h) => el("th", {}, h)))),
    el("tbody", {}, rows.map((row, i) => el("tr", { class: highlight === i ? "hl" : "" },
      row.map((cell) => el("td", {}, cell ?? "n/a")))))));
}

const ci = (pair) => (pair ? `${pair[0]}–${pair[1]}%` : "n/a");
const num = (value) => (value === null || value === undefined ? "n/a" : value);

function renderEvaluation(results) {
  const view = $("#view-eval");
  const { stress, natural, sensitivity } = results;
  const extra = progressionEvidence(results);
  if (!stress) {
    view.replaceChildren(el("div", { class: "empty" }, el("h2", {}, "No evaluation results found"),
      el("p", {}, "Run python3 scripts/run_c4_eval.py to generate them.")));
    return;
  }
  const base = stress.baseline_unverified_reference;
  const rows = [["baseline", base.hallucination_rate, base.cognitive_mismatch_rate,
    `${base.cases_with_violation}/${stress.cases}`, ci(stress.baseline_cases_with_violation_ci95), "—"]];
  for (const [name, item] of Object.entries(stress.conditions_after_repair)) {
    const m = item.mcnemar_vs_baseline;
    rows.push([name, item.hallucination_rate, item.cognitive_mismatch_rate,
      `${item.cases_with_violation}/${stress.cases}`, ci(item.cases_with_violation_ci95),
      `${m.fixed} fixed / ${m.worsened} worse, p=${m.p_exact}`]);
  }
  const bars = el("div", { class: "bars" }, rows.map((row) => el("div", { class: "bargroup" },
    el("div", { class: "bname" }, CONDITION_LABELS[row[0]]),
    barRow("Hallucination", row[1]), barRow("Cognitive mismatch", row[2]))));

  const det = stress.detection;
  const detRows = [["Factual violations", "factual"], ["Cognitive (all)", "cognitive_all"],
    ["Bloom mismatch", "bloom_mismatch"], ["Unmastered prerequisite", "unmastered_prerequisite"]]
    .map(([label, key]) => [label, det[key].tp, det[key].fp, det[key].fn,
      num(det[key].precision), num(det[key].recall), num(det[key].f1)]);

  const sections = [
    el("div", { class: "banner" }, el("b", {}, "Read before presenting: "), stress.caveat, " Labels: ", stress.label_provenance, "."),
    block("Controlled stress test",
      `${stress.cases} cases (${stress.targets} concepts × ${stress.profiles.length} learner profiles), ${stress.claims} claims. ` +
      "Baseline rates come from the reference labels; repaired rates are re-measured by the verifier.",
      el("div", {},
        el("div", { class: "legend" },
          el("span", {}, el("i", { style: "background:var(--series-fact)" }), "Hallucination rate"),
          el("span", {}, el("i", { style: "background:var(--series-cog)" }), "Cognitive-mismatch rate")),
        bars,
        table(["Condition", "Halluc. %", "Cog. mismatch %", "Cases with violation", "95% CI", "McNemar vs baseline"],
          rows.map((r) => [CONDITION_LABELS[r[0]], ...r.slice(1)]), 3))),
    block("Verifier detection against reference labels", "Initial claims, full C4. Perfect scores here show the rules behave as specified on a recipe-built corpus, not generalisation.",
      table(["Dimension", "TP", "FP", "FN", "Precision", "Recall", "F1"], detRows)),
    block("Rewrite loop", null, el("p", {}, `${stress.rewrite.corrected} of ${stress.rewrite.claims_sent} violating claims corrected `,
      `(${pct(stress.rewrite.success_rate)}); new violations introduced: ${stress.rewrite.new_violations_introduced}.`)),
  ];

  if (natural) {
    sections.push(block("Natural generation (Qwen3 4B, exploratory)",
      `${natural.explanations} cached explanations, ${natural.claims} claims. No reference labels exist, so this measures how much the rules flag, not accuracy.`,
      el("div", {},
        table(["Measure", "Before C4", "After C4"], [
          ["Claims not graph-supported", pct(natural.before.hallucination_rate), pct(natural.after.hallucination_rate)],
          ["Cognitive mismatch", pct(natural.before.cognitive_mismatch_rate), pct(natural.after.cognitive_mismatch_rate)],
          ["Inconclusive claims", natural.before.inconclusive, natural.after.inconclusive]]),
        natural.examples.map((item) => el("div", { class: "example" }, el("code", {}, item.case_id),
          el("p", {}, el("b", {}, "Qwen: "), item.original), el("p", {}, el("b", {}, "After C4: "), item.final))))));
  }
  if (sensitivity) {
    const current = state.meta.config_defaults.entail_similarity;
    sections.push(block("Entailment-threshold sensitivity",
      "Stress-test F1 is stable for thresholds 0.4–0.6, supporting the 0.6 default; natural output stays flagged because the matcher is strict about paraphrase.",
      table(["Similarity threshold", "Stress precision", "Stress recall", "Stress F1", "Natural % not graph-supported"],
        sensitivity.map((r) => [r.entail_similarity, num(r.stress_factual_precision), num(r.stress_factual_recall),
          num(r.stress_factual_f1), `${r.natural_not_graph_supported_pct}%`]),
        sensitivity.findIndex((r) => r.entail_similarity === current))));
  }
  sections.push(block("Known limitations", null, el("ul", { class: "limits" },
    el("li", {}, "Factual checking is rule-based graph-statement matching, not NLI; it cannot separate a faithful paraphrase from an invention."),
    el("li", {}, "A claim is a whole sentence, not an atomic proposition."),
    el("li", {}, "The Bloom estimator is a verb-cue heuristic; it was scored against 90 items labelled by one annotator, so agreement with independent annotators is unknown."),
    el("li", {}, "The progression results come from simulated learners whose parameters are assumptions; a human pilot is still required."),
    el("li", {}, "No independent human annotation or Cohen's kappa yet; post-repair rates reuse the same verifier."),
    el("li", {}, "C1, C2 and C3 outputs are mocked with compatible fixtures; real integration is pending."))));
  sections.splice(sections.length - 1, 0, ...extra);
  view.replaceChildren(...sections);
}

let evaluationLoaded = false;
async function loadEvaluation() {
  if (evaluationLoaded) return;
  $("#view-eval").replaceChildren(el("p", { class: "hint" }, "Loading evaluation results…"));
  try {
    renderEvaluation(await api("/api/results"));
    evaluationLoaded = true;
  } catch (error) {
    $("#view-eval").replaceChildren(el("p", { class: "error" }, error.message));
  }
}

/* ---------- inputs tab ---------- */
const FIXTURE_NOTE = "Fixture: interface-compatible mock until the upstream component is integrated.";

function inputCard(title, source, lede, ...body) {
  return el("section", { class: "block" },
    el("h3", {}, title), el("p", { class: "lede" }, source, " ", lede), ...body);
}

function renderInputs() {
  const view = $("#view-inputs");
  if (!state.meta) return;
  const target = targetInfo();
  const learner = state.learner;
  const name = (id) => state.meta.concepts[id] || id;

  const c3 = target.path;
  const steps = table(["Step", "Kind", "Concept", "Difficulty", "Prerequisites"],
    c3.path.map((step) => [step.step, step.kind, step.name, step.difficulty,
      step.prerequisites.map(name).join(", ") || "none"]));

  const ids = [...new Set([...target.graph_context.map((item) => item.id), ...Object.keys(learner.mastery)])];
  const c2 = table(["Concept", "Mastery", "Uncertainty"],
    ids.map((id) => [name(id),
      learner.mastery[id] === undefined ? "no history" : learner.mastery[id].toFixed(2),
      learner.uncertainty[id] === undefined ? "no history" : learner.uncertainty[id].toFixed(2)]));

  const c1 = target.graph_context.map((item) => el("div", { class: "ctx" },
    el("h4", {}, item.name, item.id === target.id ? " (target)" : ""),
    el("p", { class: "hint" }, "Difficulty ", item.difficulty, " · prerequisites: ",
      item.prerequisites.map(name).join(", ") || "none"),
    el("ul", { class: "plain" }, item.facts.map((fact) => el("li", {}, "True: ", fact))),
    el("ul", { class: "plain" }, item.known_false.map((fact) => el("li", { class: "false" }, "Known false: ", fact)))));

  view.replaceChildren(
    inputCard("C3: verified learning path", "From Component 3.",
      `Learner ${c3.learner_id}, target ${name(c3.target)}, verified: ${c3.verified}, source: ${c3.source}. ${FIXTURE_NOTE}`, steps),
    inputCard("C2: learner state", "From Component 2.",
      `Learner ${learner.learner_id}. These are the values the cognitive check uses (edit them in the left panel).`, c2),
    inputCard("C1: knowledge-graph evidence", "From Component 1.",
      `Statements for the concepts on the path; the factual check matches claims against these. ${FIXTURE_NOTE}`, c1));
}


/* ---------- Bloom progression tab ---------- */
const BLOOM_NAMES = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"];
const SESSION_ERROR = "Could not run the session.";

function freshJourney() { return { history: [], last: null, next: null, busy: false, error: "" }; }

function conceptBloom() { return (state.learner.bloom || {})[state.target] || { level: 0, attempts: [] }; }

function svgEl(tag, attrs, text) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

/* Line chart: series = [{ name, cls, values }]; every series shares the x labels. */
function lineChart(series, xLabels, { min = 0, max = 6, label = "" } = {}) {
  const W = 560, H = 250, L = 34, R = 86, T = 14, B = 30;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img", "aria-label": label });
  const x = (i) => L + (xLabels.length > 1 ? (i * (W - L - R)) / (xLabels.length - 1) : (W - L - R) / 2);
  const y = (v) => T + ((max - v) * (H - T - B)) / (max - min);
  for (let v = Math.ceil(min); v <= max; v += 1) {
    svg.append(svgEl("line", { class: v === min ? "axis" : "grid", x1: L, x2: W - R, y1: y(v), y2: y(v) }),
      svgEl("text", { x: L - 7, y: y(v) + 4, "text-anchor": "end" }, v));
  }
  xLabels.forEach((text, i) => {
    if (xLabels.length > 10 && i % 2 === 1) return;
    svg.append(svgEl("text", { x: x(i), y: H - 9, "text-anchor": "middle" }, text));
  });
  const ends = [];
  for (const line of series) {
    const points = line.values.map((v, i) => [x(i), y(v)]);
    svg.append(svgEl("path", { class: `ln ${line.cls}`, d: points.map(([px, py], i) => `${i ? "L" : "M"}${px.toFixed(1)} ${py.toFixed(1)}`).join(" ") }));
    points.forEach(([px, py]) => svg.append(svgEl("circle", { class: `pt ${line.cls}`, cx: px, cy: py, r: xLabels.length > 12 ? 2 : 3.5 })));
    const [lx, ly] = points[points.length - 1];
    ends.push({ x: lx + 8, y: ly + 4, name: line.name });
  }
  // End labels keep their vertical order and are pushed apart when the lines finish close together.
  ends.sort((a, b) => a.y - b.y).forEach((end, i, all) => {
    if (i && end.y < all[i - 1].y + 13) end.y = all[i - 1].y + 13;
    svg.append(svgEl("text", { x: end.x, y: end.y }, end.name));
  });
  return svg;
}

function levelBar(level, target) {
  return el("div", { class: "journey", role: "list", "aria-label": "Bloom levels" }, BLOOM_NAMES.map((name, index) => {
    const n = index + 1;
    const done = n <= level, isTarget = n === target;
    return el("div", { class: `lvl${done ? " done" : ""}${isTarget ? " target" : ""}`, role: "listitem" },
      el("b", {}, name), el("small", {}, done ? "demonstrated" : isTarget ? "target" : " "));
  }));
}

function decisionLine(decision, prefix) {
  if (!decision) return null;
  return el("div", { class: "decision" }, prefix ? el("b", {}, prefix) : null,
    badge("info", "action", decision.action),
    badge("info", "aim", `${decision.target_name} (${decision.target_level})`),
    badge("", "support", decision.scaffold, "Scaffolding fades with consecutive passes and returns after a failure."),
    el("span", { class: "hint" }, decision.reason));
}

function refreshProgressionView() {
  if (state.journey && $("#view-progress") && !$("#view-progress").hidden) renderProgression();
}

async function startSession() {
  const journey = state.journey;
  journey.busy = true; journey.error = "";
  renderProgression();
  try {
    const report = await api("/api/session", { target: state.target, source: "template", learner: state.learner, config: readConfig() });
    journey.last = { report, answered: false };
    journey.next = null;
  } catch (error) {
    journey.error = error.message || SESSION_ERROR;
  } finally {
    journey.busy = false;
    renderProgression();
  }
}

async function answerCheck(score) {
  const journey = state.journey;
  const report = journey.last.report;
  journey.busy = true; journey.error = "";
  renderProgression();
  try {
    const result = await api("/api/answer", {
      target: state.target, learner: state.learner, level: report.check.level, score,
      scaffold: report.check.scaffold, session: report.session,
    });
    state.learner = { ...state.learner, ...result.learner };
    journey.history.push({
      session: report.session, asked: report.check.level, score, action: report.progression.action,
      scaffold: report.check.scaffold, demonstrated: result.concept_progress.level,
    });
    journey.last.answered = true;
    journey.next = result.next;
    renderLearnerSummary();
  } catch (error) {
    journey.error = error.message || SESSION_ERROR;
  } finally {
    journey.busy = false;
    renderProgression();
  }
}

function renderProgression() {
  const view = $("#view-progress");
  if (!state.meta || !state.journey) return;
  const journey = state.journey;
  const target = targetInfo();
  const record = conceptBloom();
  const live = journey.last && !journey.last.answered ? journey.last.report.check : null;
  const aim = journey.next ? journey.next.target_level : live ? live.level : 0;
  const blocks = [];

  const sessionNo = journey.last && !journey.last.answered ? journey.last.report.session : record.attempts.length + 1;
  const controls = el("div", { class: "row" },
    el("button", { type: "button", class: "primary", disabled: journey.busy || (journey.last && !journey.last.answered),
      onclick: startSession }, journey.busy ? "Working…" : `Start session ${sessionNo}`),
    el("button", { type: "button", class: "ghost", disabled: journey.busy, onclick: () => {
      delete state.learner.bloom?.[state.target];
      state.journey = freshJourney();
      renderLearnerSummary();
      renderProgression();
    } }, "Reset this concept"));
  blocks.push(block(`Bloom journey: ${target.name}`,
    "Progression adds time to the check: C4 aims one Bloom level above what the learner has shown, but only when the " +
    "prerequisites are mastered. Edit mastery in the left panel (for example set a prerequisite below 0.7) to watch the policy " +
    "switch between advancing and consolidating.",
    el("div", {}, levelBar(record.level, aim),
      decisionLine(journey.next, "Next:") || decisionLine(journey.last && !journey.last.answered ? journey.last.report.progression : null, "This session:"),
      controls, journey.error ? el("p", { class: "error" }, journey.error) : null)));

  if (journey.last) {
    const report = journey.last.report;
    const clean = report.unresolved_claims.length === 0;
    const question = el("div", { class: "qcard" },
      el("div", { class: "qhead" }, badge("info", "check question", `${report.check.level_name} (level ${report.check.level})`),
        badge("", "support", report.check.scaffold)),
      el("p", { class: "qtext" }, report.check.question),
      report.check.hints.length ? el("ul", { class: "hints" }, report.check.hints.map((hint) => el("li", {}, hint))) : null,
      journey.last.answered ? el("p", { class: "hint" }, "Answer recorded. Start the next session to see the policy respond.")
        : el("div", { class: "answers" }, el("span", { class: "lab" }, "Simulate the learner's answer:"),
            el("button", { type: "button", class: "good", disabled: journey.busy, onclick: () => answerCheck(0.9) }, "Answered well"),
            el("button", { type: "button", class: "mid", disabled: journey.busy, onclick: () => answerCheck(0.55) }, "Partly"),
            el("button", { type: "button", class: "low", disabled: journey.busy, onclick: () => answerCheck(0.2) }, "Not yet")));
    blocks.push(block(`Session ${report.session}: verified explanation`,
      "Drafted for the target level, then verified and repaired. Detail fades as the learner keeps passing.",
      el("div", {}, finalDocument(report, clean), question)));
  }

  if (journey.history.length) {
    const labels = journey.history.map((row) => `S${row.session}`);
    const chart = lineChart([
      { name: "asked", cls: "t", values: journey.history.map((row) => row.asked) },
      { name: "demonstrated", cls: "d", values: journey.history.map((row) => row.demonstrated) },
    ], labels, { label: "Asked and demonstrated Bloom level by session" });
    blocks.push(block("Trajectory this run", "The level C4 asked at, and the level the learner has demonstrated after each answer.",
      el("div", { class: "timeline" },
        el("div", { class: "legend" }, el("span", {}, el("i", { class: "t" }), "asked (target)"), el("span", {}, el("i", { class: "d" }), "demonstrated")),
        chart,
        table(["Session", "Action", "Support", "Asked", "Score", "Demonstrated after"],
          journey.history.map((row) => [row.session, row.action, row.scaffold,
            BLOOM_NAMES[row.asked - 1], row.score.toFixed(2), BLOOM_NAMES[row.demonstrated - 1] || "none"])))));
  }
  view.replaceChildren(...blocks);
}

/* ---------- progression evidence (Evaluation tab) ---------- */
const MODEL_LABELS = {
  zpd: "ZPD learner (design hypothesis)", flat: "Flat control", matched: "Matched control",
};
const COND_STYLE = { A_unverified: ["A: unverified", "a"], B_current_c4: ["B: current C4", "b"], C_progressive: ["C: progressive", "c"] };
const signed = (value) => (value > 0 ? `+${value}` : String(value));
const pText = (p) => (p === null || p === undefined ? "n/a" : p < 0.0001 ? "<0.0001" : String(p));

function progressionEvidence(results) {
  const data = results.progression;
  if (!data) return [];
  const { rq1, rq2 } = data;
  const names = { unverified: "Unverified explanation", static_c4: "Static C4 (current)", progressive_c4: "Progressive C4" };
  const out = [];
  out.push(el("div", { class: "banner" }, el("b", {}, "Progression evidence: "), rq2.caveat));
  out.push(block("RQ1: faithful and at the target Bloom level",
    `${rq1.cases} stress cases × ${rq1.learner_starts.length} learner starts = ${rq1.runs} runs. ${rq1.caveat}`,
    table(["Text", "Question at target level", "95% CI", "Runs with a violation", "Halluc. %", "Cog. mismatch %"],
      Object.entries(rq1.conditions).map(([key, row]) => [names[key], pct(row.question_at_target_level_pct), ci(row.question_at_target_level_ci95),
        `${row.runs_with_violation}/${row.runs}`, row.hallucination_rate, row.cognitive_mismatch_rate]))));

  const holder = el("div");
  let model = "zpd";
  const paint = () => {
    const entry = rq2.models[model];
    const sessions = rq2.config.sessions;
    const labels = Array.from({ length: sessions }, (_, i) => `S${i + 1}`);
    const series = Object.entries(COND_STYLE).map(([key, [name, cls]]) => ({
      name, cls, values: entry.conditions[key].trajectory_mean_true_level }));
    const all = series.flatMap((line) => line.values);
    const low = Math.max(0, Math.floor(Math.min(...all)) - 0), high = Math.min(6, Math.ceil(Math.max(...all)));
    const pairedRows = Object.entries(entry.paired).map(([key, row]) => [key.replaceAll("_", " "),
      signed(row.mean_difference), row.ci95_bootstrap ? `${row.ci95_bootstrap[0]} to ${row.ci95_bootstrap[1]}` : "n/a",
      pText(row.wilcoxon.p), row.cohens_dz ?? "n/a", `${row.learners_better} / ${row.learners_worse} / ${row.learners_equal}`]);
    holder.replaceChildren(
      el("div", { class: "seg", role: "group", "aria-label": "Learner model" }, Object.entries(MODEL_LABELS).map(([key, text]) =>
        el("button", { type: "button", "aria-pressed": String(key === model), onclick: () => { model = key; paint(); } }, text))),
      el("div", { class: "legend" }, Object.values(COND_STYLE).map(([name, cls]) => el("span", {}, el("i", { class: cls }), name))),
      lineChart(series, labels, { min: low, max: Math.max(high, low + 1), label: "Mean true Bloom level by session" }),
      table(["Condition", "Final level", "Capability gain", "Reached level 3", "Too hard %", "Too easy %"],
        Object.keys(entry.conditions).map((key) => { const row = entry.conditions[key];
          return [key.replaceAll("_", " "), row.mean_final_level, row.mean_capability_gain, pct(row.share_reaching_level_3_pct),
            row.sessions_too_hard_pct, row.sessions_too_easy_pct]; })),
      el("h4", { class: "ctx" }, "Paired comparisons (capability gain, positive favours the first)"),
      table(["Comparison", "Mean diff.", "95% bootstrap CI", "Wilcoxon p", "Cohen's dz", "Better / worse / equal"], pairedRows));
  };
  paint();
  out.push(block("RQ2: does progression raise the demonstrated level across sessions?",
    `${rq2.config.learners} simulated learners, ${rq2.config.sessions} sessions, seeded and paired. The flat and matched controls show where the mechanism does not help.`,
    holder));

  out.push(block("Sensitivity to study length (C minus B)", "Capability gain difference with a 95% bootstrap interval.",
    table(["Sessions", "ZPD", "Flat", "Matched"], Object.entries(rq2.sensitivity_sessions).map(([n, row]) => [n,
      ...["zpd", "flat", "matched"].map((m) => `${signed(row[m].mean_difference)} (${row[m].ci95_bootstrap[0]} to ${row[m].ci95_bootstrap[1]})`)]))));

  if (results.bloom) {
    const rows = [];
    for (const [split, entry] of Object.entries(results.bloom.splits)) {
      for (const version of ["v1", "v2"]) {
        const r = entry[version];
        rows.push([`${split} · ${version}`, r.items, pct(r.accuracy), ci(r.accuracy_ci95), pct(r.within_one), r.mean_abs_error, r.macro_f1]);
      }
    }
    out.push(block("Bloom-level estimator against labelled items", results.bloom.caveat,
      table(["Split · estimator", "Items", "Accuracy", "95% CI", "Within one level", "Mean abs. error", "Macro-F1"], rows)));
  }
  return out;
}

/* ---------- tabs and boot ---------- */
function selectTab(name) {
  if (name === "inputs") renderInputs();
  if (name === "progress") renderProgression();
  for (const id of ["verify", "progress", "inputs", "eval"]) {
    $(`#tab-${id}`).setAttribute("aria-selected", String(id === name));
    $(`#view-${id}`).hidden = id !== name;
  }
  if (name === "eval") loadEvaluation();
}

async function boot() {
  $("#tab-verify").addEventListener("click", () => selectTab("verify"));
  $("#tab-progress").addEventListener("click", () => selectTab("progress"));
  $("#tab-inputs").addEventListener("click", () => selectTab("inputs"));
  $("#tab-eval").addEventListener("click", () => selectTab("eval"));
  $("#target").addEventListener("change", applyTarget);
  $("#preset").addEventListener("change", applyPreset);
  $("#explanation").addEventListener("input", updateCount);
  $("#explanation").addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); run(); }
  });
  $("#run").addEventListener("click", () => run());
  $("#run-empty").addEventListener("click", () => run());
  $("#auto-template").addEventListener("click", () => run("template"));
  $("#auto-ollama").addEventListener("click", () => run("ollama"));
  $("#reset").addEventListener("click", () => { applyTarget(); resetConfig(); showError(""); });
  document.querySelectorAll("[data-scenario]").forEach((b) =>
    b.addEventListener("click", () => loadScenario(b.dataset.scenario)));
  $("#gen-template").addEventListener("click", () => generate("template"));
  $("#gen-ollama").addEventListener("click", () => generate("ollama"));
  ["#cfg-attempts", "#cfg-mastery", "#cfg-uncertainty"].forEach((id) => $(id).addEventListener("input", syncConfigLabels));
  $("#gen-ollama").disabled = true;
  $("#auto-ollama").disabled = true;
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
  if (location.hash === "#run") run();
  if (location.hash === "#eval") selectTab("eval");  // deep link used for demos and screenshots
  if (location.hash === "#progress") selectTab("progress");
  api("/api/health").then((health) => {
    const { online, model_installed: installed, model } = health.ollama;
    state.ollamaReady = online && installed;
    $("#gen-ollama").disabled = !state.ollamaReady;
    $("#auto-ollama").disabled = !state.ollamaReady;
    $("#gen-ollama").title = state.ollamaReady ? "Generate a draft with the local model" : "Start Ollama and install qwen3:4b to enable";
    setChip("#chip-ollama", state.ollamaReady, online ? (installed ? model : `${model} missing`) : "Ollama offline");
  }).catch(() => setChip("#chip-ollama", false, "Ollama offline"));
}

boot();
