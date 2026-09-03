# Phase 2 Mobile Inbox & Rescued Revenue Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the contractor user experience into a mobile-first 3-tab layout with an iMessage-style chat drawer and a live Rescued Revenue ROI counter.

**Architecture:** Frontend rewrite of main dashboard panels in `index.html`, dynamic revenue calculation engine, threaded chat drawer with quick-reply buttons and one-tap dialer, synced with existing Supabase backend.

**Tech Stack:** HTML5, Tailwind CSS, FontAwesome 6, Vanilla JavaScript, Supabase REST API.

**Spec:** `docs/superpowers/specs/2026-09-02-mobile-inbox-revenue-tracker-design.md`

## Global Constraints
- Must remain fully responsive on 375px+ mobile phone displays.
- Large touch targets (minimum 44px height) for work-glove usability.
- Zero extra dependencies or build steps; pure single-file frontend client in `index.html`.

---

### Task 1: 3-Tab Contractor Navigation & Rescued Revenue Banner

**Files:**
- Modify: `index.html`

- [x] **Step 1: Add 3-Tab Main Navigation Bar (Inbox / Rescued ROI / Quick Controls)**
- [x] **Step 2: Add Rescued Revenue Quick Banner above Inbox**
- [x] **Step 3: Implement dynamic calculation of Rescued Revenue ($) based on avg job value**

---

### Task 2: iMessage/WhatsApp Style Conversation Drawer

**Files:**
- Modify: `index.html`

- [x] **Step 1: Build the slide-over conversation drawer with contact header and 1-tap call button**
- [x] **Step 2: Render conversational chat bubbles (inbound vs outbound AI response)**
- [x] **Step 3: Add quick-reply chips ("On my way!", "Can I call in 10 mins?", "What is your address?")**
- [x] **Step 4: Connect SMS reply form to `/api/sms/send` and refresh thread**

---

### Task 3: Rescued Revenue ROI Tab & Quick Controls Tab

**Files:**
- Modify: `index.html`

- [x] **Step 1: Build Tab 2 (Rescued ROI Tracker with job value slider, ROI multiple calculation, and breakdown)**
- [x] **Step 2: Build Tab 3 (Quick Controls with Master Automation toggle and alert phone setting)**
- [x] **Step 3: Wire up tab switching and settings persistence**

---

### Task 4: End-to-End Verification & Production Push

**Files:**
- Test: Verify on browser & mobile viewport
- Git commit and push to `main` for Vercel deployment
