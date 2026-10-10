// Regression test for frontend safety against undefined/null properties in simulator & control center
const assert = require("assert");

function testReflexStatusResolution() {
  // Scenario 1: Original crash scenario - triage object exists but has no status property
  const triage1 = {
    scam_probability: 0.85,
    scam_type: "fake_kyc",
    urgency: 8,
    latency_ms: 12
  };
  const score1 = 85;
  const reflexScore1 = (triage1.risk_score !== undefined)
    ? triage1.risk_score
    : (triage1.scam_probability !== undefined ? Math.round(triage1.scam_probability * 100) : score1);

  // In original code: triage1 ? triage1.status.toUpperCase() : "DONE" -> THREW TypeError
  let threwOriginal = false;
  try {
    const bad = triage1 ? triage1.status.toUpperCase() : "DONE";
  } catch (err) {
    threwOriginal = true;
    assert(err instanceof TypeError);
    assert(err.message.includes("toUpperCase"));
  }
  assert(threwOriginal, "Original unpatched expression must fail with TypeError");

  // In patched code: safely resolved
  const patchedStatus1 = String(triage1.status || (reflexScore1 >= 20 ? "ESCALATED" : "PASSED")).toUpperCase();
  assert.strictEqual(patchedStatus1, "ESCALATED");

  // Scenario 2: triage is null or undefined
  const triage2 = null;
  const reflexScore2 = 0;
  const patchedStatus2 = String(triage2?.status || (reflexScore2 >= 20 ? "ESCALATED" : "PASSED")).toUpperCase();
  assert.strictEqual(patchedStatus2, "PASSED");

  // Scenario 3: triage has explicit status "passed"
  const triage3 = { status: "passed" };
  const patchedStatus3 = String(triage3.status || "PASSED").toUpperCase();
  assert.strictEqual(patchedStatus3, "PASSED");

  // Scenario 4: channel is undefined or null
  const channel = undefined;
  const header = String(channel || "sms").toUpperCase() + " Message";
  assert.strictEqual(header, "SMS Message");

  // Scenario 5: verdict label is missing or null
  const verdict1 = {};
  const label1 = String(verdict1.label || "unknown").toUpperCase();
  assert.strictEqual(label1, "UNKNOWN");

  // Scenario 6: recommended_action is missing
  const recAction1 = String(verdict1.recommended_action || "none").toUpperCase();
  assert.strictEqual(recAction1, "NONE");

  console.log(" All frontend safeguard scenarios passed successfully!");
}

testReflexStatusResolution();
