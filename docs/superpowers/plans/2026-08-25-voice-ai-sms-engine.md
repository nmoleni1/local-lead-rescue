# Phase 1 Voice AI & 2-Way SMS Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy the 2-Way Voice AI Receptionist & Missed-Call Auto-Text Engine with flexible arrival windows and Supabase persistence.

**Architecture:** Python WSGI serverless backend (`api/index.py`) handling Twilio Voice TwiML, speech gathering, and 2-way SMS webhooks; Supabase PostgreSQL schema (`leads`, `calls`, `messages`); frontend dashboard with live call simulation and message thread rendering.

**Tech Stack:** Python 3.10+, Twilio TwiML / REST API, Supabase PostgreSQL, Vanilla JS / Tailwind CSS.

**Spec:** `docs/superpowers/specs/2026-08-25-voice-ai-sms-engine-design.md`

## Global Constraints
- Python backend must remain zero-dependency/standard-library compatible with Vercel serverless functions.
- All database operations route through Supabase REST with auto-cleansed URL and Service Key.
- No mandatory calendar OAuth required for contractors; arrival windows are safe defaults (`Morning`, `Afternoon`, `Emergency`).

---

### Task 1: Supabase Database Schema Extensions

**Files:**
- Modify: `api/index.py`
- Test: `tests/test_db_schema.py`

**Interfaces:**
- Consumes: `SUPABASE_URL`, `SUPABASE_KEY`
- Produces: `calls` table, `messages` table, `address` & `preferred_window` columns in `leads`

- [ ] **Step 1: Write test verifying schema and table accessibility**

```python
# tests/test_db_schema.py
import urllib.request
import json
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gylegafrbyroktpjumli.supabase.co").strip().rstrip('/')
if SUPABASE_URL.endswith('/rest/v1'):
    SUPABASE_URL = RAW_URL[:-8]
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5bGVnYWZyYnlyb2t0cGp1bWxpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzY5NDQ5NSwiZXhwIjoyMTAzMjcwNDk1fQ.J9hLv9nPhJEOxF0BclA3TRMtA5t0zcy73cYWgu5nfLM").strip()

def test_supabase_tables():
    url = f"{SUPABASE_URL}/rest/v1/leads?select=*"
    req = urllib.request.Request(url, headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
```

- [ ] **Step 2: Run test to verify basic connection**
Run: `python -m unittest tests/test_db_schema.py`

- [ ] **Step 3: Add schema helpers in `api/index.py` for calls and messages**
Add `log_call()`, `get_messages_for_lead()`, `add_message()` functions to `api/index.py`.

- [ ] **Step 4: Commit schema changes**
```bash
git add api/index.py tests/test_db_schema.py
git commit -m "feat: add calls and 2-way messages database helpers"
```

---

### Task 2: Inbound Voice AI Receptionist & TwiML Endpoints

**Files:**
- Modify: `api/index.py`
- Test: `tests/test_voice_endpoints.py`

**Interfaces:**
- Consumes: Twilio Voice webhook payloads (`From`, `CallSid`, `SpeechResult`)
- Produces: TwiML XML responses with `<Say>`, `<Gather>`, and `<Hangup>`

- [ ] **Step 1: Write test for `/api/voice/inbound` and `/api/voice/gather`**

```python
# tests/test_voice_endpoints.py
import unittest
from api.index import handle_api_request

class TestVoiceEndpoints(unittest.TestCase):
    def test_inbound_voice_twiml(self):
        status, res = handle_api_request("POST", "/api/voice/inbound", "")
        self.assertEqual(status, 200)
        self.assertIn("response_type", res)
        self.assertEqual(res.get("response_type"), "twiml")
```

- [ ] **Step 2: Implement Voice AI logic in `api/index.py`**
Implement conversational prompts, greeting, and extraction of caller name, problem, and preferred arrival window.

- [ ] **Step 3: Verify tests pass**
Run: `python -m unittest tests/test_voice_endpoints.py`

- [ ] **Step 4: Commit**
```bash
git add api/index.py tests/test_voice_endpoints.py
git commit -m "feat: implement Twilio Voice AI receptionist endpoints"
```

---

### Task 3: 2-Way SMS Inbound Webhook & Contractor Push Alerts

**Files:**
- Modify: `api/index.py`
- Test: `tests/test_sms_inbound.py`

**Interfaces:**
- Consumes: `POST /api/sms/inbound` with `From`, `Body`
- Produces: Threaded message insertion in Supabase + automated contractor cell notification

- [ ] **Step 1: Write test for incoming SMS handling**
- [ ] **Step 2: Implement SMS webhook parser and contractor alert dispatcher**
- [ ] **Step 3: Verify tests pass**
- [ ] **Step 4: Commit**
```bash
git add api/index.py tests/test_sms_inbound.py
git commit -m "feat: implement 2-way SMS inbound webhook with contractor alerts"
```

---

### Task 4: Frontend UI Updates (Voice Simulator & Arrival Window Badges)

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `/api/leads` payload containing `address`, `preferred_window`, `messages`
- Produces: Live arrival window badges, voice call simulator modal, and threaded message previews

- [ ] **Step 1: Update Lead Cards to display Address & Arrival Window badges**
- [ ] **Step 2: Add "Simulate Voice Call" action in Simulator Modal**
- [ ] **Step 3: Push changes to GitHub and verify on Vercel**
```bash
git add index.html
git commit -m "feat: add voice call simulator and arrival window UI indicators"
```
