# Phase 3 Bilingual (English / Spanish) Auto-Responder Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automatic Spanish language detection, Spanish AI SMS templates, Polly.Lupe bilingual Voice AI synthesis, language badges, and dual-language quick-reply chips.

**Files Affected:**
- `api/index.py`: Add language detection, Spanish trade SMS generators, bilingual TwiML endpoints, and contractor Spanish alert notifications.
- `index.html`: Add `🇲🇽 ES` badge rendering, English/Spanish quick-reply toggle in conversation drawer, and bilingual toggle in Quick Controls.
- `tests/test_bilingual.py`: Unit tests verifying language detection, Spanish TwiML generation, and Spanish SMS drafting.

## Tasks

### Task 1: Backend Language Detection & Spanish AI SMS Templates
- [x] Add `detect_language(text)` helper in `api/index.py`
- [x] Update `generate_ai_sms_draft(name, service, notes, language="en")` to generate natural Spanish SMS for Plumbing, HVAC, Electrical, and General repairs
- [x] Update `/api/webhook/lead` and `/api/sms/inbound` to auto-detect language and respond in the customer's language

### Task 2: Bilingual Voice AI Receptionist
- [x] Update `/api/voice/inbound` greeting with bilingual prompt
- [x] Update `/api/voice/gather` to detect Spanish speech, respond using `<Say voice="Polly.Lupe" language="es-US">`, and classify Spanish arrival windows (*"Emergencia inmediata"*, *"Ventana de la mañana"*, etc.)
- [x] Tag lead with `language: "es"` and push Spanish alert to contractor

### Task 3: Frontend Bilingual Badges & Dual Quick Reply Chips
- [x] Render `🇲🇽 ES` or `🇺🇸 EN` badge on lead cards
- [x] Add language switcher tabs to Quick Reply chips in Conversation Drawer (`🇺🇸 English` / `🇲🇽 Español`)
- [x] Add `[🌐 Bilingual Engine]` toggle to Quick Controls tab

### Task 4: Unit Testing, Verification & Production Deployment
- [x] Write unit tests in `tests/test_bilingual.py`
- [x] Commit, push to `main`, and verify live deployment on Vercel
