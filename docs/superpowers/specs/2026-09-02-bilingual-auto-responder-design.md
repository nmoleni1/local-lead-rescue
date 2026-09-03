# Phase 3 Design Spec: Bilingual (English / Spanish) Auto-Responder & Voice AI

**Date**: 2026-09-02  
**Topic**: Bilingual SMS Engine, Spanish Language Detection, Polly.Lupe Voice Synthesis, and Contractor Bilingual Controls  
**Target Market**: West Valley City, UT (38%+ Hispanic Demographic)  

---

## 1. Executive Summary & Problem
In West Valley City, Utah, over 38% of the population identifies as Hispanic or Latino. When a homeowner experiences an emergency water leak or furnace breakdown, they frequently text or call in Spanish:
> *"Hola, tengo una emergencia con el calentador de agua que se está saliendo. ¿Tienen a alguien disponible hoy?"*

Standard English-only auto-responders fail to convert these leads, losing thousands in potential ticket value to bilingual competitors.

**Phase 3** solves this by equipping LeadRescue AI with:
1. **Automatic Language Detection**: Detects Spanish in inbound SMS messages, web submissions, and voice calls.
2. **Adaptive Spanish AI SMS Follow-ups**: Formats contextual, culturally resonant Spanish follow-ups matching the trade requested.
3. **Bilingual Voice AI Receptionist**: Polly.Lupe neural voice response in `es-US` when Spanish speech or prompt is detected, with Spanish confirmation and emergency window scheduling.
4. **Contractor Language Badges & Dual Quick Replies**: `🇲🇽 ES` / `🇺🇸 EN` badges on lead cards, and 1-tap Spanish field quick replies (`¡En camino!`, `¿Puedo llamar en 10 min?`, `¿Cuál es su dirección?`).

---

## 2. Technical Architecture

```
Inbound Lead (Call, SMS, Web Form)
       │
       ▼
[Language Detector in api/index.py]
  ├── Spanish keyword density check (hola, emergencia, fuga, calentador, agua, etc.)
  │
  ├──► IF SPANISH DETECTED:
  │      ├─ Tag lead: language = 'es'
  │      ├─ Voice AI: speaks Spanish TwiML via Polly.Lupe (es-US)
  │      ├─ SMS Auto-Responder: replies with localized Spanish trade message
  │      └─ Contractor Alert: "🚨 Lead en Español (Spanish Lead): [Phone] necesita [Service]"
  │
  └──► IF ENGLISH DETECTED (or Default):
         ├─ Tag lead: language = 'en'
         ├─ Voice AI: speaks English TwiML via Polly.Joanna (en-US)
         ├─ SMS Auto-Responder: replies with English trade message
         └─ Contractor Alert: standard English alert
```

---

## 3. Core Requirements

### 3.1 Backend (`api/index.py`)
- `detect_language(text)`: Analyzes input strings for Spanish tokens and accents.
- `generate_ai_sms_draft(name, service, notes, language='en')`:
  - When `language == 'es'`, outputs natural Spanish responses for Plumbing, HVAC, Electrical, and Roofing.
- `/api/voice/inbound`:
  - Bilingual voice greeting: *"Hi! Thanks for calling [Company]. For English, please speak. Para español, hable en español."*
- `/api/voice/gather`:
  - Checks if `SpeechResult` is Spanish. If so, answers using `<Say voice="Polly.Lupe" language="es-US">` and formats the Spanish dispatch window.
- `/api/sms/inbound`:
  - Detects language from `Body`, appends `[ES]` or `[EN]` to lead notes, and replies in the matched language.

### 3.2 Frontend (`index.html`)
- Lead cards display `🇲🇽 ES` badge if Spanish, `🇺🇸 EN` if English.
- Quick Controls panel includes:
  - `[🌐 Bilingual Auto-Detection Active]` switch.
  - Default Spanish SMS template preview.
- Conversation Drawer includes:
  - Language toggle for Quick Reply chips: `[🇺🇸 English Chips | 🇲🇽 Spanish Chips]`!
  - 1-tap Spanish replies:
    - `🏃 ¡En camino! (Llegada en 20 mins)`
    - `📞 Estoy en un trabajo. ¿Le puedo llamar en 10 min?`
    - `📍 ¿Cuál es la dirección exacta de su casa?`
    - `💰 Ofrecemos estimados gratuitos hoy.`
