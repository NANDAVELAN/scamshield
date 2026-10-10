/**
 * ScamShield Background Service Worker (MV3)
 */

const BACKEND_URL = "http://localhost:8080";

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "analyze") {
    analyzeMessage(message.payload)
      .then(result => sendResponse({ status: "success", data: result }))
      .catch(error => sendResponse({ status: "error", message: error.message }));
    return true; // Keep channel open for async response
  }

  if (message.action === "check_url") {
    checkUrlSafety(message.url)
      .then(result => sendResponse({ status: "success", data: result }))
      .catch(error => sendResponse({ status: "error", message: error.message }));
    return true;
  }

  if (message.action === "get_recent_incidents") {
    fetch(`${BACKEND_URL}/incidents`)
      .then(res => res.json())
      .then(data => sendResponse({ status: "success", data }))
      .catch(error => sendResponse({ status: "error", message: error.message }));
    return true;
  }
});

async function analyzeMessage(payload) {
  try {
    const response = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend returned HTTP ${response.status}`);
    }

    const data = await response.json();
    
    // Save to local storage for popup
    chrome.storage.local.get({ recent_verdicts: [] }, (res) => {
      const list = [data, ...res.recent_verdicts.slice(0, 9)];
      chrome.storage.local.set({ recent_verdicts: list });
    });

    return data;
  } catch (err) {
    console.error("ScamShield analyze error:", err);
    throw err;
  }
}

async function checkUrlSafety(url) {
  // Check against backend via quick analyze or local known list
  const payload = {
    channel: "web",
    sender: "browser_navigation",
    body: `Visiting website: ${url}`,
    urls: [url]
  };
  return await analyzeMessage(payload);
}
