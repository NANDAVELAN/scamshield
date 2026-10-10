# ScamShield Repository Cleanup Plan

## Objective
Streamline the repository so that the only user-facing front-ends remaining are:
1. **The Phone Application** (`app/`)
2. **The Message & Attack Simulator** (`simulator/`)

All unnecessary and redundant front-ends and superseded components are removed/archived, while preserving 100% of the runtime dependencies, backend endpoints, multi-agent pipeline, and test suites needed by the two kept front-ends.

---

## 1. KEEP List (Preserved at Runtime)

### 1.1 Front-Ends Kept
- **Phone Application**:
  - `app/`
    - `app/android/`: Complete native Android project (Gradle, manifests, Kotlin bridge plugins: `MainActivity.kt`, `NotificationBridgePlugin.kt`, `ScamNotificationListenerService.kt`).
    - `app/www/index.html`: Mobile application UI (feed, sealed cards, reflex/agent inspection, settings, backend connectivity).
    - `app/capacitor.config.json`: Capacitor bridge configuration.
    - `app/package.json` & `app/package-lock.json`: Mobile dependencies (`@capacitor/android`, `@capacitor/core`, `@capacitor/cli`, `@typesafe-ai/sdk`).
    - `app/typesafe_triage.mjs` & `app/typesafe_triage.d.ts`: Mobile reflex triage client module.
  - `.github/workflows/build-apk.yml`: CI workflow to build Android debug APK.
- **Message & Attack Simulator**:
  - `simulator/`
    - `simulator/index.html`: Interactive attack simulator UI.
    - `simulator/app.js`: Simulator logic (presets, `/analyze` call, SSE live logs, incident approval/rejection/undo actions).
    - `simulator/styles.css`: Simulator styling.

### 1.2 Backend & Multi-Agent Runtime Dependencies
- **Core Server & API**:
  - `server/main.py`: Canonical FastAPI application (`/analyze`, `/analyze/stream`, `/health`, `/incidents`, `/incidents/{id}/approve`, `/reject`, `/undo`, and static mounting for `/simulator`).
  - `server/store.py`: In-memory thread-safe incident storage (`incident_store`).
  - `server/executor.py`: Human-in-the-loop reversible action executor (`executor`).
  - `server/cache.py`: SHA-256 message-hash verdict cache (`verdict_cache`).
  - `server/__init__.py`.
- **Google ADK Multi-Agent Package**:
  - `scamshield_agent/agent.py`: Root sequential and parallel agent graph (`build_root_agent`).
  - `scamshield_agent/schemas.py`: Core Pydantic schemas (`AnalyzeRequest`, `AnalyzeResponse`, `Verdict`, `Evidence`, `Incident`, `TriageResult`).
  - `scamshield_agent/prompts.py`: Agent prompts (extractor, url, sender, attachment, verdict, incident).
  - `scamshield_agent/tools/`: Domain tools (`entities.py`, `url_tools.py`, `sender_tools.py`, `attachment_tools.py`, `campaign_tools.py`, `incident_tools.py`).
  - `scamshield_agent/data/`: Mock datasets (`brands.json`, `domain_reputation.json`, `sender_reputation.json`, `blocklist.json`).
  - `scamshield_agent/__init__.py`.
- **Safety Guardrails**:
  - `guardrails/`: Deterministic 5-layer guardrail system (`input_guard.py`, `tool_guard.py`, `output_guard.py`, `action_policy.py`, `redact.py`, `defang.py`, `__init__.py`).
- **LLM Router & Fallback Chain**:
  - `llm/`: Multi-tier router (`router.py`, `providers.py`, `__init__.py`) with Gemini Pro -> Gemini Flash -> OpenRouter -> Ollama -> Rules fallback.
- **Reflex Triage**:
  - `triage/`: System-1 reflex triage (`quick_triage`, `jev_client.py`, `rules.py`, `__init__.py`).
- **Evaluation Harness & Invariants**:
  - `harness/`: Safety test harness (`invariants.py`, `report.py`, `run.py`, `suites/golden.json`, `suites/adversarial.json`).
- **Configuration & Setup**:
  - `.env.example`, `.env`, `.gitignore`, `Dockerfile`, `requirements.txt`, `pytest.ini`, `package.json`, `package-lock.json`, `AGENTS.md`, `README.md`, `PITCH.md`, `document.md`.
  - Startup scripts: `start.bat`, `start.sh`, `start.ps1` (updated to launch Simulator directly).
- **Test Suite**:
  - `tests/test_pipeline.py`, `tests/test_router.py`, `tests/test_triage.py`, `tests/test_tools.py`, `tests/test_harness.py`, `tests/test_typesafe_sdk.mjs`, `tests/test_frontend_safeguards.js`, `tests/sample_messages.json`, `tests/rehearse_e2e.py`.

---

## 2. Removal Plan (Items to Move to `_archive/` or Delete)

### (a) Front-Ends We Are Dropping (Move to `_archive/`)
| Path | Reason | What Depends On It |
|---|---|---|
| `control_center/` (`index.html`, `app.js`, `styles.css`) | Operator Mission Control front-end being dropped (only keeping Phone App + Simulator). | Nothing outside `server/control.py`. |
| `extension/` (`manifest.json`, `background.js`, `content_gmail.js`, `popup.html`, `popup.js`, `warning.html`) | Chrome MV3 browser extension front-end being dropped. | Nothing. |

### (b) Duplicate or Superseded Files (Move to `_archive/`)
| Path | Reason | What Depends On It |
|---|---|---|
| `scamshield-mobile.html` | Exact byte-for-byte duplicate (25,825 bytes) of `app/www/index.html` located in root. | Nothing (active mobile app lives in `app/`). |
| `backend/` (`app.py`, `agent_graph.py`, `guardrails.py`, `reflex.py`, `router.py`, `rules_engine.py`, `schemas.py`, `tools.py`, `requirements.txt`, `.env.example`, `run.bat`, `run.sh`, `tests/`) | Superseded standalone backend prototype; duplicate implementation of `server/`, `scamshield_agent/`, `guardrails/`, `llm/`, and `triage/`. | Nothing in the kept phone app or simulator (both connect to canonical `server/main.py`). |

### (c) Dead Code & Unused Endpoints (Move to `_archive/` or Clean Up)
| Path / Target | Reason | What Depends On It |
|---|---|---|
| `server/control.py` | API router `/control/*` used exclusively by the dropped `control_center` UI. | Nothing (only imported by `server/main.py` for control endpoints). |
| `server/main.py` lines mounting `/control/ui` and redirecting `/` to `/control/ui` | Dead routes pointing to the removed Control Center UI. | Redirect updated to `/simulator`. |
| `start.bat`, `start.sh`, `start.ps1` references to `http://127.0.0.1:8080/control/ui` | Dead links pointing to removed Control Center UI. | Updated to launch `http://127.0.0.1:8080/simulator`. |

### (d) Generated / Temporary Files (Delete Permanently)
| Path | Reason | What Depends On It |
|---|---|---|
| `**/__pycache__/` | Python bytecode cache files. | Generated runtime artifacts; safe to delete. |
| `.pytest_cache/` | Pytest session cache. | Generated runtime artifacts; safe to delete. |
| `app/android/.gradle/` | Gradle build daemon and cache binaries. | Generated build cache; safe to delete. |
| `app/android/build/` | Gradle build reports and output binaries. | Generated build output; safe to delete. |
| `harness/harness_report.html` | Generated evaluation report artifact. | Generated by `harness/run.py`; safe to regenerate. |

### (e) Dependencies in `requirements.txt` / `package.json`
- **`requirements.txt`**: All 8 packages (`google-adk`, `fastapi`, `uvicorn`, `pydantic`, `httpx`, `python-dotenv`, `pytest`, `litellm`) are required by the kept backend runtime. None are unused.
- **Root `package.json`**: Keeps `@typesafe-ai/sdk` (needed by `tests/test_typesafe_sdk.mjs`).
- **`app/package.json`**: Keeps `@capacitor/android`, `@capacitor/core`, `@capacitor/cli`, `@typesafe-ai/sdk` (needed by phone app).

---

## 3. Transition & Compatibility Assurance
1. **Unified Backend Compatibility**: Ensure `server/main.py` `/analyze` response provides all fields expected by both `simulator/app.js` and `app/www/index.html`.
2. **Simulator Default Route**: Redirect `GET /` to `/simulator` so opening the server opens the kept Simulator.
3. **Archive Preservation**: All non-generated items (`control_center/`, `extension/`, `backend/`, `scamshield-mobile.html`, `server/control.py`) are moved into `_archive/` maintaining directory structure, ensuring 100% reversibility.
4. **Documentation Updates**: Update `README.md` and `AGENTS.md` to reflect that the Phone App and Simulator are the two active user interfaces.
