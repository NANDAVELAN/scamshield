const BACKEND_URL = "http://localhost:8080";

document.addEventListener("DOMContentLoaded", () => {
  const statusBadge = document.getElementById("status-badge");
  const quickInput = document.getElementById("quick-input");
  const btnScan = document.getElementById("btn-scan");
  const scanResult = document.getElementById("scan-result");
  const recentList = document.getElementById("recent-list");
  const btnControlCenter = document.getElementById("btn-control-center");

  // Health check
  fetch(`${BACKEND_URL}/health`)
    .then(r => r.json())
    .then(data => {
      statusBadge.textContent = "ACTIVE";
      statusBadge.className = "badge badge-online";
    })
    .catch(() => {
      statusBadge.textContent = "OFFLINE";
      statusBadge.className = "badge badge-offline";
    });

  // Load recent verdicts
  chrome.storage.local.get({ recent_verdicts: [] }, (res) => {
    renderRecent(res.recent_verdicts);
  });

  // Scan action
  btnScan.addEventListener("click", async () => {
    const text = quickInput.value.trim();
    if (!text) return;

    btnScan.disabled = true;
    btnScan.textContent = "Scanning...";
    scanResult.style.display = "none";

    try {
      const response = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel: "extension",
          sender: "popup-quick-scan",
          body: text,
          urls: extractUrls(text)
        })
      });

      const data = await response.json();
      btnScan.disabled = false;
      btnScan.textContent = "⚡ Reflex Scan";

      scanResult.style.display = "block";
      const isDangerous = data.verdict.risk_score >= 60;
      scanResult.style.background = isDangerous ? "rgba(239, 68, 68, 0.2)" : "rgba(34, 197, 94, 0.2)";
      scanResult.style.color = isDangerous ? "#fca5a5" : "#86efac";
      scanResult.style.border = `1px solid ${isDangerous ? "#ef4444" : "#22c55e"}`;
      scanResult.innerHTML = `
        <strong>${data.verdict.label.toUpperCase()} (${data.verdict.risk_score}/100)</strong><br>
        ${data.verdict.explanation_en.slice(0, 100)}...
      `;

      chrome.storage.local.get({ recent_verdicts: [] }, (res) => {
        const list = [data, ...res.recent_verdicts.slice(0, 4)];
        chrome.storage.local.set({ recent_verdicts: list });
        renderRecent(list);
      });
    } catch (err) {
      btnScan.disabled = false;
      btnScan.textContent = "⚡ Reflex Scan";
      scanResult.style.display = "block";
      scanResult.style.background = "rgba(239, 68, 68, 0.2)";
      scanResult.style.color = "#fca5a5";
      scanResult.textContent = "Scan error: " + err.message;
    }
  });

  btnControlCenter.addEventListener("click", () => {
    chrome.tabs.create({ url: "http://localhost:8080/control/ui" });
  });

  function renderRecent(items) {
    if (!items || items.length === 0) {
      recentList.innerHTML = `<div style="color: var(--muted); font-size: 11px;">No recent incidents intercepted yet.</div>`;
      return;
    }

    recentList.innerHTML = items.slice(0, 4).map(item => {
      const v = item.verdict;
      const score = v.risk_score;
      const pillClass = score >= 60 ? "risk-high" : (score >= 35 ? "risk-med" : "risk-low");
      const summary = (item.incident_id || "Scan").slice(0, 14);
      return `
        <div class="recent-item">
          <span style="font-size: 12px; max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${v.explanation_en}
          </span>
          <span class="risk-pill ${pillClass}">${v.label}</span>
        </div>
      `;
    }).join("");
  }

  function extractUrls(text) {
    const regex = /https?:\/\/[^\s<>"]+/g;
    return text.match(regex) || [];
  }
});
