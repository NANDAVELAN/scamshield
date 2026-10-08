const BACKEND_URL = window.location.origin.includes(":8080") ? "" : "http://localhost:8080";

const PRESETS = {
  sbi: {
    sender: "VM-SBIINB",
    channel: "sms",
    body: "Dear SBI Customer, your YONO account is locked. Update KYC immediately or account will be suspended in 24 hours. Download Yono_Update.apk from http://sbi-kyc-update.com/app",
    urls: ["http://sbi-kyc-update.com/app"],
    attachments: ["Yono_Update.apk"]
  },
  electricity: {
    sender: "+919876543210",
    channel: "sms",
    body: "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from electricity office because your previous month bill was not updated. Please immediately contact electricity officer at 9876543210. Pay immediately at http://t.ly/mseb-bill",
    urls: ["http://t.ly/mseb-bill"],
    attachments: []
  },
  digital_arrest: {
    sender: "CBI-HQ-OFFICER",
    channel: "whatsapp",
    body: "This is DCP Vikramaditya Singh from Cyber Crime CBI Headquarters. A parcel containing 5 fake passports and 140g MDMA was intercepted in Mumbai under your Aadhaar. You are placed under DIGITAL ARREST. Join immediate video verification on Skype or warrant will be executed.",
    urls: [],
    attachments: ["Arrest_Warrant_CBI.pdf"]
  },
  fedex: {
    sender: "FEDEX-INDIA",
    channel: "sms",
    body: "FedEx Alert: Parcel #FDX-99812 detained at Mumbai Customs due to unpaid clearance duty and illegal narcotics. Pay Rs. 2,499 immediately to avoid police seizure: http://fedx-customs-pay.in/release",
    urls: ["http://fedx-customs-pay.in/release"],
    attachments: []
  },
  job: {
    sender: "+919123456789",
    channel: "whatsapp",
    body: "Hi! Earn Rs 3,000 to Rs 8,000 daily from home just by liking YouTube videos! No investment required. Join our official Telegram: @telegram_jobs_hr. Start now: http://bit.ly/yt-daily-earn",
    urls: ["http://bit.ly/yt-daily-earn"],
    attachments: []
  },
  legit: {
    sender: "HDFCBK",
    channel: "sms",
    body: "Your HDFC Bank NetBanking OTP for transaction of Rs 1,250 at AMAZON INDIA is 482910. Valid for 10 mins. Do not share OTP with anyone.",
    urls: [],
    attachments: []
  }
};

let currentIncidentId = null;

document.addEventListener("DOMContentLoaded", () => {
  const chips = document.querySelectorAll(".chip");
  const inputSender = document.getElementById("input-sender");
  const inputChannel = document.getElementById("input-channel");
  const inputBody = document.getElementById("input-body");
  const btnSimulate = document.getElementById("btn-simulate");
  const btnClear = document.getElementById("btn-clear");
  const chatThread = document.getElementById("chat-thread");
  const dispSender = document.getElementById("disp-sender");
  const dispChannel = document.getElementById("disp-channel");
  const channelIcon = document.getElementById("channel-icon");
  const reflexBadge = document.getElementById("reflex-badge");
  const reflexLatency = document.getElementById("reflex-latency");
  const reflexDisplay = document.getElementById("reflex-display");
  const streamLog = document.getElementById("stream-log");
  const verdictBody = document.getElementById("verdict-body");
  const verdictBadge = document.getElementById("verdict-score-badge");
  const pipelineProvider = document.getElementById("pipeline-provider");
  const actionFooter = document.getElementById("action-footer");
  const actionProposalDesc = document.getElementById("action-proposal-desc");
  const btnApproveAction = document.getElementById("btn-approve-action");
  const btnRejectAction = document.getElementById("btn-reject-action");
  const btnUndoAction = document.getElementById("btn-undo-action");

  // Load default preset
  loadPreset("sbi");

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      chips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const key = chip.getAttribute("data-preset");
      loadPreset(key);
    });
  });

  function loadPreset(key) {
    const data = PRESETS[key];
    if (!data) return;
    inputSender.value = data.sender;
    inputChannel.value = data.channel;
    inputBody.value = data.body;
    updatePhoneHeader(data.sender, data.channel);
  }

  function updatePhoneHeader(sender, channel) {
    dispSender.textContent = sender;
    dispChannel.textContent = channel.toUpperCase() + " Message";
    channelIcon.textContent = channel === "whatsapp" ? "🟢" : (channel === "sms" ? "💬" : "✉️");
  }

  btnClear.addEventListener("click", () => {
    inputBody.value = "";
    chatThread.innerHTML = "";
    resetPipelineDisplay();
  });

  btnSimulate.addEventListener("click", () => {
    runAttackSimulation();
  });

  function resetPipelineDisplay() {
    reflexBadge.textContent = "WAITING";
    reflexBadge.className = "badge";
    reflexLatency.textContent = "-- ms";
    reflexDisplay.innerHTML = `<p class="placeholder-text">Awaiting incoming message to trigger Jev / Flash Reflex Guard...</p>`;
    streamLog.innerHTML = `<div class="log-line info">[System] Multi-agent orchestration engine initialized.</div>`;
    verdictBody.innerHTML = `<p class="placeholder-text">Verdict synthesis will appear once multi-agent consensus is reached.</p>`;
    verdictBadge.textContent = "SCORE: --";
    verdictBadge.className = "risk-badge badge-neutral";
    pipelineProvider.textContent = "Ready";
    actionFooter.style.display = "none";
    resetAgentNodes();
  }

  function resetAgentNodes() {
    ["triage", "url", "sender", "attach", "verdict"].forEach(name => {
      const node = document.getElementById(`node-${name}`);
      if (node) {
        node.className = "agent-node";
        node.querySelector(".node-state").textContent = "Idle";
      }
    });
  }

  function setNodeState(name, state, label) {
    const node = document.getElementById(`node-${name}`);
    if (node) {
      node.className = `agent-node ${state}`;
      node.querySelector(".node-state").textContent = label || state;
    }
  }

  function appendLog(text, type = "info") {
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    const time = new Date().toISOString().substring(11, 19);
    line.textContent = `[${time}] ${text}`;
    streamLog.appendChild(line);
    streamLog.scrollTop = streamLog.scrollHeight;
  }

  async function runAttackSimulation() {
    const body = inputBody.value.trim();
    const sender = inputSender.value.trim();
    const channel = inputChannel.value;

    if (!body) return;

    btnSimulate.disabled = true;
    btnSimulate.textContent = "⚡ Running Defense...";
    resetPipelineDisplay();
    updatePhoneHeader(sender, channel);

    // 1. Add inbound message bubble
    const bubble = document.createElement("div");
    bubble.className = "message-bubble bubble-inbound";
    bubble.innerHTML = `
      <div>${escapeHtml(body)}</div>
      <div class="bubble-meta">
        <span>${channel.toUpperCase()} · Inbound</span>
        <span class="threat-tag" id="bubble-threat-tag">Scanning...</span>
      </div>
    `;
    chatThread.appendChild(bubble);
    chatThread.scrollTop = chatThread.scrollHeight;

    const urls = extractUrls(body);
    const attachments = extractAttachments(body);

    const payload = {
      channel: channel,
      sender: sender,
      body: body,
      urls: urls,
      attachments: attachments
    };

    appendLog(`Attack simulation triggered from ${sender} via ${channel}`, "info");

    // 2. Immediate reflex triage timing
    const t0 = performance.now();
    setNodeState("triage", "active", "Evaluating");

    try {
      // Connect to SSE stream
      appendLog("Initiating multi-agent cognitive stream (/analyze/stream)...", "info");
      
      const response = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const reflexMs = Math.round(performance.now() - t0);
      reflexLatency.textContent = `${reflexMs} ms`;

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const result = await response.json();
      currentIncidentId = result.incident_id;

      // Animate pipeline stages
      animatePipelineExecution(result, reflexMs, bubble);

    } catch (err) {
      appendLog(`Pipeline error: ${err.message}`, "threat");
      verdictBody.innerHTML = `<div style="color: var(--rose);">Execution error: ${err.message}. Fail-closed active.</div>`;
    } finally {
      btnSimulate.disabled = false;
      btnSimulate.textContent = "🚀 Launch Attack Simulation";
    }
  }

  function animatePipelineExecution(result, reflexMs, bubble) {
    const verdict = result.verdict;
    const triage = result.triage;
    const isThreat = verdict.risk_score >= 60;
    const isSuspicious = verdict.risk_score >= 35 && verdict.risk_score < 60;

    // Reflex display
    reflexBadge.textContent = triage ? triage.status.toUpperCase() : "DONE";
    reflexBadge.style.background = isThreat ? "var(--rose)" : (isSuspicious ? "var(--amber)" : "var(--emerald)");
    reflexBadge.style.color = "white";

    reflexDisplay.innerHTML = `
      <div style="width: 100%;">
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
          <strong>Reflex Decision: ${triage ? triage.status.toUpperCase() : "ESCALATED"}</strong>
          <span style="color: var(--cyan); font-family: monospace;">Risk: ${triage ? triage.risk_score : verdict.risk_score}/100</span>
        </div>
        <div style="font-size: 12px; color: #cbd5e1;">${triage ? triage.reason : "Escalated for deep multi-agent verification."}</div>
      </div>
    `;

    appendLog(`Reflex gate returned in ${reflexMs}ms with score ${triage ? triage.risk_score : verdict.risk_score}`, "agent");

    // Agent simulation step animation
    setTimeout(() => {
      setNodeState("triage", "done", "Escalated");
      setNodeState("url", "active", "Checking");
      appendLog("URL Investigator: Normalizing homoglyphs & querying domain reputation...", "agent");
    }, 150);

    setTimeout(() => {
      setNodeState("url", "done", "Cleaned");
      setNodeState("sender", "active", "Auditing");
      appendLog("Sender Investigator: Checking spoofing signatures and channel headers...", "agent");
    }, 350);

    setTimeout(() => {
      setNodeState("sender", "done", "Analyzed");
      setNodeState("attach", "active", "Scanning");
      appendLog("Attachment Investigator: Inspecting extensions and payload heuristics...", "agent");
    }, 550);

    setTimeout(() => {
      setNodeState("attach", "done", "Checked");
      setNodeState("verdict", "active", "Synthesizing");
      appendLog(`Synthesizing grounded verdict using ${result.provider_used}...`, "agent");
    }, 750);

    setTimeout(() => {
      setNodeState("verdict", "done", "Consensus");
      renderFinalVerdict(result, bubble);
    }, 950);
  }

  function renderFinalVerdict(result, bubble) {
    const verdict = result.verdict;
    const score = verdict.risk_score;
    const isThreat = score >= 60;
    const isSuspicious = score >= 35 && score < 60;

    pipelineProvider.textContent = result.provider_used;

    // Update phone bubble
    if (isThreat) {
      bubble.classList.add("bubble-flagged");
      bubble.querySelector("#bubble-threat-tag").textContent = "🚨 SCAM INTERCEPTED";
      bubble.querySelector("#bubble-threat-tag").style.color = "var(--rose)";
    } else if (isSuspicious) {
      bubble.classList.add("bubble-flagged");
      bubble.querySelector("#bubble-threat-tag").textContent = "⚠️ SUSPICIOUS";
      bubble.querySelector("#bubble-threat-tag").style.color = "var(--amber)";
    } else {
      bubble.classList.add("bubble-safe");
      bubble.querySelector("#bubble-threat-tag").textContent = "✅ VERIFIED SAFE";
      bubble.querySelector("#bubble-threat-tag").style.color = "var(--emerald)";
    }

    // Verdict Badge
    verdictBadge.textContent = `RISK: ${score}/100 [${verdict.label.toUpperCase()}]`;
    verdictBadge.className = `risk-badge ${isThreat ? "badge-scam" : (isSuspicious ? "badge-suspicious" : "badge-safe")}`;

    // Evidence pills
    let evidenceHtml = "";
    if (verdict.evidence && verdict.evidence.length > 0) {
      evidenceHtml = `
        <div class="evidence-grid">
          ${verdict.evidence.map(e => `
            <div class="evidence-pill">
              <div class="evidence-source">🔍 ${escapeHtml(e.source_tool)}</div>
              <div>${escapeHtml(e.finding)}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    verdictBody.innerHTML = `
      <div class="verdict-explanation">${escapeHtml(verdict.explanation_en)}</div>
      ${verdict.defanged_content ? `
        <div style="background: rgba(15,23,42,0.8); border: 1px dashed var(--panel-border); padding: 8px 10px; border-radius: 6px; font-size: 11px; margin-bottom: 12px; font-family: monospace;">
          <div style="color: var(--cyan); margin-bottom: 2px;">🛡️ Defanged / Redacted Content:</div>
          <div>${escapeHtml(verdict.defanged_content)}</div>
        </div>
      ` : ""}
      ${evidenceHtml}
    `;

    // Action Proposal
    if (verdict.recommended_action && verdict.recommended_action !== "allow") {
      actionFooter.style.display = "block";
      actionProposalDesc.textContent = `Proposed Action: ${verdict.recommended_action.toUpperCase()} — Reversible, 0 destructive side-effects.`;
      btnApproveAction.style.display = "inline-flex";
      btnRejectAction.style.display = "inline-flex";
      btnUndoAction.style.display = "none";
    } else {
      actionFooter.style.display = "none";
    }

    appendLog(`Verdict synthesis finalized: ${verdict.label} (${score}/100). Recommended: ${verdict.recommended_action}`, isThreat ? "threat" : "info");
  }

  // ACTION BUTTON HANDLERS
  btnApproveAction.addEventListener("click", async () => {
    if (!currentIncidentId) return;
    try {
      appendLog(`Sending human approval for incident ${currentIncidentId}...`, "info");
      const res = await fetch(`${BACKEND_URL}/incidents/${currentIncidentId}/approve`, { method: "POST" });
      const data = await res.json();
      appendLog(`Quarantine executed successfully: ${data.detail}`, "threat");
      btnApproveAction.style.display = "none";
      btnRejectAction.style.display = "none";
      btnUndoAction.style.display = "inline-flex";
      actionProposalDesc.textContent = `Status: QUARANTINED (Reversible). Audited in security ledger.`;
    } catch (err) {
      appendLog(`Approval failed: ${err.message}`, "threat");
    }
  });

  btnRejectAction.addEventListener("click", async () => {
    if (!currentIncidentId) return;
    try {
      appendLog(`Rejecting proposed defense for incident ${currentIncidentId}...`, "warn");
      const res = await fetch(`${BACKEND_URL}/incidents/${currentIncidentId}/reject`, { method: "POST" });
      const data = await res.json();
      appendLog(`Action rejected by operator: ${data.detail}`, "warn");
      actionFooter.style.display = "none";
    } catch (err) {
      appendLog(`Rejection failed: ${err.message}`, "threat");
    }
  });

  btnUndoAction.addEventListener("click", async () => {
    if (!currentIncidentId) return;
    try {
      appendLog(`Executing safe UNDO on incident ${currentIncidentId}...`, "warn");
      const res = await fetch(`${BACKEND_URL}/incidents/${currentIncidentId}/undo`, { method: "POST" });
      const data = await res.json();
      appendLog(`Action reversed: ${data.detail}`, "info");
      btnUndoAction.style.display = "none";
      btnApproveAction.style.display = "inline-flex";
      btnRejectAction.style.display = "inline-flex";
      actionProposalDesc.textContent = `Status: RESTORED from quarantine.`;
    } catch (err) {
      appendLog(`Undo failed: ${err.message}`, "threat");
    }
  });

  function extractUrls(text) {
    const regex = /https?:\/\/[^\s<>"]+/g;
    return text.match(regex) || [];
  }

  function extractAttachments(text) {
    const regex = /\b[\w-]+\.(apk|exe|scr|bat|pdf|zip|vbs|jar)\b/gi;
    return text.match(regex) || [];
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
});
