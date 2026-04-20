"use strict";

const POLL_INTERVAL_MS = 15000;

/* ── Setup Wizard ─────────────────────────────────────── */

var _wizardCurrentStep = 1;
var _wizardSelectedAgent = null;

var AGENT_CONFIGS = {
    "claude-code": {
        label: "Paste into ~/.claude/settings.json",
        config: JSON.stringify({
            hooks: {
                PreToolUse: [
                    { matcher: ".*", hooks: [
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/env-guard.py" },
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/spending-guard.py" },
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/credential-scope-guard.py" },
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/fork-scope-guard.py" },
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/build-gate.py" }
                    ]}
                ],
                PostToolUse: [
                    { matcher: ".*", hooks: [
                        { type: "command", command: "python3 $TAG_HOME/tag/hooks/memory-autosave.py" }
                    ]}
                ]
            }
        }, null, 2)
    },
    "codex": {
        label: "Add to your codex config (codex.json or ~/.codex/config.json)",
        config: JSON.stringify({
            hooks: {
                pre_exec: [
                    "python3 $TAG_HOME/tag/hooks/env-guard.py",
                    "python3 $TAG_HOME/tag/hooks/spending-guard.py",
                    "python3 $TAG_HOME/tag/hooks/credential-scope-guard.py",
                    "python3 $TAG_HOME/tag/hooks/fork-scope-guard.py",
                    "python3 $TAG_HOME/tag/hooks/build-gate.py"
                ],
                post_exec: [
                    "python3 $TAG_HOME/tag/hooks/memory-autosave.py"
                ]
            }
        }, null, 2)
    },
    "cursor": {
        label: "Add to Cursor settings (Settings > Features > Terminal hooks)",
        config: [
            "# Pre-execution hooks — add each line as a separate hook command",
            "python3 $TAG_HOME/tag/hooks/env-guard.py",
            "python3 $TAG_HOME/tag/hooks/spending-guard.py",
            "python3 $TAG_HOME/tag/hooks/credential-scope-guard.py",
            "python3 $TAG_HOME/tag/hooks/fork-scope-guard.py",
            "python3 $TAG_HOME/tag/hooks/build-gate.py",
            "",
            "# Post-execution hook",
            "python3 $TAG_HOME/tag/hooks/memory-autosave.py"
        ].join("\n")
    },
    "other": {
        label: "General pattern — pipe tool calls through TaG hooks before execution",
        config: [
            "# In your agent's pre-execution hook, pipe stdin through each guard:",
            "export TAG_HOME=/path/to/TaG",
            "",
            "# Required: set TAG_HOME to your TaG repo location, then add these",
            "# as pre-execution hooks in your agent's configuration:",
            "python3 $TAG_HOME/tag/hooks/env-guard.py",
            "python3 $TAG_HOME/tag/hooks/spending-guard.py",
            "python3 $TAG_HOME/tag/hooks/credential-scope-guard.py",
            "python3 $TAG_HOME/tag/hooks/fork-scope-guard.py",
            "python3 $TAG_HOME/tag/hooks/build-gate.py",
            "",
            "# Post-execution (memory auto-save):",
            "python3 $TAG_HOME/tag/hooks/memory-autosave.py",
            "",
            "# Each hook reads JSON from stdin: {\"tool_name\": \"...\", \"tool_input\": {...}}",
            "# and writes JSON to stdout: {\"decision\": \"block\"|\"allow\", \"reason\": \"...\"}"
        ].join("\n")
    }
};

function selectAgent(agent) {
    _wizardSelectedAgent = agent;
    var cards = document.querySelectorAll(".agent-card");
    cards.forEach(function(c) {
        c.classList.toggle("selected", c.getAttribute("onclick") === "selectAgent('" + agent + "')");
    });
    var cfg = AGENT_CONFIGS[agent];
    if (!cfg) return;
    document.getElementById("config-block-label").textContent = cfg.label;
    document.getElementById("config-pre").textContent = cfg.config;
    document.getElementById("config-block").style.display = "";
}

function copyConfig() {
    var pre = document.getElementById("config-pre");
    if (!pre) return;
    navigator.clipboard.writeText(pre.textContent).then(function() {
        var btn = document.getElementById("btn-copy");
        if (btn) { btn.textContent = "Copied!"; setTimeout(function() { btn.textContent = "Copy"; }, 1800); }
    });
}

function copyVerifyCmd() {
    var pre = document.getElementById("verify-cmd");
    if (!pre) return;
    navigator.clipboard.writeText(pre.textContent).then(function() {
        var btns = document.querySelectorAll("#wizard-step-3 .btn-copy");
        btns.forEach(function(b) { b.textContent = "Copied!"; setTimeout(function() { b.textContent = "Copy"; }, 1800); });
    });
}

function _setWizardStep(step) {
    _wizardCurrentStep = step;
    for (var i = 1; i <= 4; i++) {
        var panel = document.getElementById("wizard-step-" + i);
        var dot   = document.querySelector(".wizard-step[data-step='" + i + "']");
        if (panel) panel.classList.toggle("active", i === step);
        if (dot)   dot.classList.toggle("active", i === step);
        if (dot)   dot.classList.toggle("done", i < step);
    }
}

function wizardNext() {
    if (_wizardCurrentStep < 4) _setWizardStep(_wizardCurrentStep + 1);
}

function wizardPrev() {
    if (_wizardCurrentStep > 1) _setWizardStep(_wizardCurrentStep - 1);
}

async function completeSetup() {
    try {
        await fetch("/api/setup-complete", { method: "POST" });
    } catch (_) {}
    showDashboard();
}

function showWizard() {
    document.getElementById("wizard-overlay").style.display = "";
    document.getElementById("main-app").style.display = "none";
}

function showDashboard() {
    document.getElementById("wizard-overlay").style.display = "none";
    document.getElementById("main-app").style.display = "";
    fetchStatus();
}



function relativeTime(isoString) {
    if (!isoString) return "\u2014";
    const now = Date.now();
    const then = new Date(isoString).getTime();
    if (isNaN(then)) return String(isoString);
    const diff = Math.floor((now - then) / 1000);
    if (diff < 5)    return "just now";
    if (diff < 60)   return diff + "s ago";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return Math.floor(diff / 86400) + "d ago";
}

function verdictClass(verdict) {
    const v = (verdict || "").toLowerCase();
    if (v === "allow") return "verdict-allow";
    if (v === "hold")  return "verdict-hold";
    if (v === "block") return "verdict-block";
    return "verdict-unknown";
}

function setHealthDot(state) {
    const dot = document.getElementById("system-health-dot");
    const label = document.getElementById("system-health-label");
    dot.className = "status-dot " + state;
    const labels = { alive: "System alive", stale: "Stale heartbeat", dead: "Offline" };
    label.textContent = labels[state] || state;
}

function makeEl(tag, className) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    return el;
}

function setText(el, text) {
    el.textContent = text;
    return el;
}

function renderGovernance(data) {
    const gov = data.governance || {};
    const statGoverned  = document.getElementById("stat-governed");
    const statAuthority = document.getElementById("stat-authority");
    const statHooks     = document.getElementById("stat-hooks");
    const badge         = document.getElementById("governed-badge");

    const isGoverned = !!gov.governed;
    statGoverned.textContent = isGoverned ? "Active" : "Inactive";
    statGoverned.className   = "stat-value " + (isGoverned ? "good" : "bad");

    statAuthority.textContent = gov.authority_matrix_loaded ? "Loaded" : "Missing";
    statAuthority.className   = "stat-value " + (gov.authority_matrix_loaded ? "good" : "warn");

    const hookCount = (data.hooks || []).filter(function(h) { return h.active; }).length;
    statHooks.textContent = String(hookCount);
    statHooks.className   = "stat-value " + (hookCount > 0 ? "good" : "warn");

    badge.textContent = isGoverned ? "Governed" : "Ungoverned";
    badge.className   = "badge " + (isGoverned ? "governed" : "ungoverned");
}

function renderMemory(data) {
    const hb  = data.heartbeat || {};
    const eng = data.engram    || {};
    const hs  = data.hindsight || {};

    document.getElementById("hb-last-pulse").textContent = relativeTime(hb.last_pulse);

    const sessionEl    = document.getElementById("hb-session");
    const sessionAlive = hb.session_alive;
    if (sessionAlive === true) {
        sessionEl.textContent  = "Alive";
        sessionEl.style.color  = "var(--accent-green)";
    } else if (sessionAlive === false) {
        sessionEl.textContent  = "Inactive";
        sessionEl.style.color  = "var(--muted)";
    } else {
        sessionEl.textContent  = "\u2014";
        sessionEl.style.color  = "";
    }

    document.getElementById("eng-count").textContent  = eng.entry_count != null ? String(eng.entry_count) : "\u2014";
    document.getElementById("eng-recent").textContent = eng.recent_tag  || "\u2014";

    document.getElementById("hs-count").textContent   = hs.total != null ? String(hs.total) : "\u2014";
    document.getElementById("hs-sources").textContent = hs.source_count != null ? hs.source_count + " src" : "\u2014";
}

function renderDecisions(data) {
    const feed      = document.getElementById("decisions-feed");
    const decisions = data.recent_decisions || [];

    while (feed.firstChild) feed.removeChild(feed.firstChild);

    if (!decisions.length) {
        feed.appendChild(setText(makeEl("div", "decisions-empty"), "No governance decisions recorded yet."));
        return;
    }

    decisions.forEach(function(d) {
        const row = makeEl("div", "decision-row");

        const verdict = makeEl("span", "decision-verdict " + verdictClass(d.verdict));
        verdict.textContent = d.verdict || "?";
        row.appendChild(verdict);

        const content = makeEl("div", "decision-content");
        const action  = d.action || d.tool || d.event || "unknown";
        content.appendChild(setText(makeEl("div", "decision-action"), action));
        const meta = d.source || d.session_id || "";
        if (meta) content.appendChild(setText(makeEl("div", "decision-meta"), meta));
        row.appendChild(content);

        row.appendChild(setText(makeEl("span", "decision-time"), relativeTime(d.timestamp || d.ts)));
        feed.appendChild(row);
    });
}

function renderHooks(data) {
    const list  = document.getElementById("hooks-list");
    const hooks = data.hooks || [];

    while (list.firstChild) list.removeChild(list.firstChild);

    if (!hooks.length) {
        list.appendChild(setText(makeEl("div", "hooks-empty"), "No hooks found."));
        return;
    }

    hooks.forEach(function(h) {
        const row = makeEl("div", "hook-row");
        row.appendChild(makeEl("span", "hook-dot " + (h.active ? "active" : "inactive")));
        row.appendChild(setText(makeEl("span", "hook-name"), h.name));
        row.appendChild(setText(makeEl("span", "hook-state"), h.active ? "active" : "off"));
        list.appendChild(row);
    });
}

function renderSetup(data) {
    const gov = data.governance || {};
    document.getElementById("setup-runtime").textContent = gov.runtime_path || "\u2014";
    document.getElementById("setup-config").textContent  = gov.config_dir   || "\u2014";

    const govEl = document.getElementById("setup-governed");
    govEl.textContent  = gov.governed ? "Enabled" : "Not active";
    govEl.style.color  = gov.governed ? "var(--accent-green)" : "var(--danger)";
}

function renderAll(data) {
    const hb       = data.heartbeat || {};
    const alive    = hb.session_alive;
    const lastPulse = hb.last_pulse ? new Date(hb.last_pulse).getTime() : null;
    const stale    = lastPulse && (Date.now() - lastPulse > 120000);

    if      (alive === true && !stale) setHealthDot("alive");
    else if (stale)                    setHealthDot("stale");
    else if (alive === false)          setHealthDot("dead");
    else                               setHealthDot("stale");

    renderGovernance(data);
    renderMemory(data);
    renderDecisions(data);
    renderHooks(data);
    renderSetup(data);
}

var _dashboardInitialized = false;

async function fetchStatus() {
    try {
        const resp = await fetch("/api/status");
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const data = await resp.json();
        const gov = data.governance || {};
        const hookCount = (data.hooks || []).length;
        if (!_dashboardInitialized) {
            _dashboardInitialized = true;
            if (!gov.governed || hookCount === 0) {
                showWizard();
                return;
            } else {
                showDashboard();
            }
        }
        renderAll(data);
    } catch (err) {
        if (!_dashboardInitialized) {
            _dashboardInitialized = true;
            showDashboard();
        }
        setHealthDot("dead");
        document.getElementById("system-health-label").textContent = "Server unreachable";
        console.error("TaG status fetch failed:", err);
    }
}

document.getElementById("btn-refresh").addEventListener("click", fetchStatus);

fetchStatus();
setInterval(fetchStatus, POLL_INTERVAL_MS);
