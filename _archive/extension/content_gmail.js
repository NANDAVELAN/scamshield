/**
 * ScamShield Gmail Content Script
 * Injects instant "Don't open" tags on inbox rows and risk banners on opened messages.
 */

console.log("[ScamShield] Gmail content script active.");

// Inject badge styles
const styleSheet = document.createElement("style");
styleSheet.textContent = `
  .scamshield-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #dc2626;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: 8px;
    letter-spacing: 0.3px;
    box-shadow: 0 2px 4px rgba(220, 38, 38, 0.3);
    animation: scamshield-pulse 2s infinite ease-in-out;
  }
  .scamshield-tag.suspicious {
    background: #d97706;
  }
  .scamshield-tag.safe {
    background: #16a34a;
  }
  @keyframes scamshield-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.9; transform: scale(1.02); }
  }
  .scamshield-banner {
    background: #1e1b4b;
    border: 2px solid #ef4444;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    color: #f8fafc;
    font-family: Roboto, Arial, sans-serif;
  }
  .scamshield-banner-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
    font-size: 14px;
    color: #f87171;
    margin-bottom: 8px;
  }
  .scamshield-banner-evidence {
    font-size: 12px;
    color: #cbd5e1;
    margin: 6px 0;
    padding-left: 12px;
    border-left: 2px solid #ef4444;
  }
  .scamshield-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
    margin-top: 8px;
    margin-right: 8px;
  }
  .scamshield-btn.reject {
    background: #475569;
  }
  .scamshield-float-btn {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #0f172a;
    color: #38bdf8;
    border: 2px solid #38bdf8;
    padding: 10px 16px;
    border-radius: 24px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    z-index: 999999;
  }
`;
document.head.appendChild(styleSheet);

// Floating analyze trigger for demonstration
const floatBtn = document.createElement("button");
floatBtn.className = "scamshield-float-btn";
floatBtn.innerHTML = "🛡️ Analyze this email (ScamShield)";
floatBtn.addEventListener("click", () => {
  scanCurrentOpenedEmail();
});
document.body.appendChild(floatBtn);

// Periodically inspect inbox rows
setInterval(() => {
  scanInboxRows();
}, 2000);

function scanInboxRows() {
  const rows = document.querySelectorAll("tr.zA:not([data-scamshield-checked])");
  rows.forEach(row => {
    row.setAttribute("data-scamshield-checked", "true");
    
    // Extract snippet and subject
    const subjectEl = row.querySelector(".bog, .y6");
    const snippetEl = row.querySelector(".y2");
    const senderEl = row.querySelector(".yW, .bA4");

    const subject = subjectEl ? subjectEl.textContent.trim() : "";
    const snippet = snippetEl ? snippetEl.textContent.trim() : "";
    const sender = senderEl ? senderEl.textContent.trim() : "";

    const fullContent = `${subject} ${snippet}`.toLowerCase();

    // High speed client-side regex reflex for instantaneous inbox tagging
    const isSuspicious = 
      fullContent.includes("kyc") ||
      fullContent.includes("block") ||
      fullContent.includes("disconnect") ||
      fullContent.includes("urgent") ||
      fullContent.includes("digital arrest") ||
      fullContent.includes("lottery") ||
      fullContent.includes("refund") ||
      fullContent.includes("cbi");

    if (isSuspicious) {
      const tag = document.createElement("span");
      tag.className = "scamshield-tag";
      tag.innerHTML = "⚠️ Don't open — flagged by ScamShield";
      if (subjectEl) {
        subjectEl.appendChild(tag);
      }
    }
  });
}

function scanCurrentOpenedEmail() {
  const bodyEl = document.querySelector(".ii.gt, .a3s.aiL, div[dir='ltr']");
  const subjectEl = document.querySelector("h2.hP");
  
  const bodyText = bodyEl ? bodyEl.innerText : document.body.innerText;
  const subjectText = subjectEl ? subjectEl.innerText : "Email Analysis";

  floatBtn.innerHTML = "⏳ Investigating with ScamShield...";

  chrome.runtime.sendMessage({
    action: "analyze",
    payload: {
      channel: "gmail",
      sender: "sender@gmail-opened.test",
      subject: subjectText,
      body: bodyText.slice(0, 1500),
      urls: extractUrls(bodyText)
    }
  }, (response) => {
    floatBtn.innerHTML = "🛡️ Analyze this email (ScamShield)";
    if (response && response.status === "success") {
      injectWarningBanner(response.data);
    } else {
      alert("ScamShield backend offline or analyzing: " + (response ? response.message : "check server"));
    }
  });
}

function extractUrls(text) {
  const regex = /https?:\/\/[^\s<>"]+/g;
  return text.match(regex) || [];
}

function injectWarningBanner(data) {
  const existing = document.querySelector(".scamshield-banner");
  if (existing) existing.remove();

  const container = document.querySelector(".nH.hx, .ii.gt") || document.body;
  const banner = document.createElement("div");
  banner.className = "scamshield-banner";

  const isHighRisk = data.verdict.risk_score >= 60;
  banner.style.borderColor = isHighRisk ? "#ef4444" : "#22c55e";

  let evidenceHtml = data.verdict.evidence.map(e => 
    `<div class="scamshield-banner-evidence">🔍 <b>${e.source_tool}:</b> ${e.finding}</div>`
  ).join("");

  banner.innerHTML = `
    <div class="scamshield-banner-header">
      <span>🛡️ ScamShield Verdict: ${(data.verdict?.label || "unknown").toUpperCase()} (Risk Score: ${data.verdict?.risk_score ?? 0}/100)</span>
      <span>Provider: ${data.provider_used || "rules"}</span>
    </div>
    <p style="margin: 6px 0; font-size: 13px;">${data.verdict.explanation_en}</p>
    ${evidenceHtml ? `<div style="margin-top: 8px;"><b>Evidence Trail:</b>${evidenceHtml}</div>` : ""}
    <div style="margin-top: 10px;">
      <button class="scamshield-btn" id="scamshield-quarantine-btn">Approve Quarantine</button>
      <button class="scamshield-btn reject" id="scamshield-dismiss-btn">Dismiss</button>
    </div>
  `;

  container.insertBefore(banner, container.firstChild);

  document.getElementById("scamshield-quarantine-btn").addEventListener("click", () => {
    fetch(`http://localhost:8080/incidents/${data.incident_id}/approve`, { method: "POST" })
      .then(res => res.json())
      .then(() => alert("Message successfully quarantined! Action audited in log."))
      .catch(err => alert("Quarantine failed: " + err));
  });

  document.getElementById("scamshield-dismiss-btn").addEventListener("click", () => {
    banner.remove();
  });
}
