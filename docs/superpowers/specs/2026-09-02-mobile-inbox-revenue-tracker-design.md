# Phase 2 Design Spec: Contractor Mobile Inbox & Rescued Revenue Redesign

**Date**: 2026-09-02  
**Topic**: Mobile-First iMessage/WhatsApp Style Inbox, Rescued Revenue ROI Tracker, and 3-Tab Contractor UX  
**Target Market**: Local Trade Contractors in West Valley City, UT  

---

## 1. Executive Summary & Problem
Local contractors work with gloves on job sites or while driving between houses. Traditional SaaS dashboards with complex filters, data tables, and developer terminology alienate tradesmen. Furthermore, contractors need to see concrete, immediate dollar justification for their \$99–\$199/month investment.

**LeadRescue AI Phase 2** delivers a radical simplification:
1. **iMessage/WhatsApp-Style Chat Drawer**: 1-tap full-screen conversation view for every lead, displaying inbound texts, AI drafts, voice transcripts, and 1-tap phone dialer.
2. **Rescued Revenue ROI Counter**: High-impact dollar value tracker displaying calculated revenue saved based on industry job values (e.g. \$850 avg plumbing job, \$1,200 avg HVAC job).
3. **Streamlined 3-Tab Navigation**:
   - `📥 Live Inbox` (Active lead cards & chat threads)
   - `💰 Rescued ROI` (Financial metrics, closed job value, ROI multiple)
   - `⚡ Quick Controls` (1-switch automation toggle, contractor alert phone setup)

---

## 2. Architecture & UX Flow

```
[Contractor Mobile Screen]
  ├── Bottom/Top Tab Navigation: [ 📥 Inbox ] [ 💰 Revenue ROI ] [ ⚡ Quick Controls ]
  │
  ├──► Tab 1: Live Inbox
  │      ├─► Rescued Revenue Quick Banner ("$3,400 Saved • 4 Leads Rescued")
  │      ├─► Lead Cards (Large touch targets, Arrival Window Badges)
  │      └─► Tap Card ──► Opens iMessage-Style Full Drawer
  │                         ├─► Speech transcript (if Voice Call)
  │                         ├─► Threaded text messages
  │                         ├─► Quick-reply chips ("On my way", "Call in 10 mins")
  │                         └─► 1-Tap "Call Customer" green button
  │
  ├──► Tab 2: Rescued Revenue Tracker
  │      ├─► Total Rescued Revenue ($)
  │      ├─► ROI Multiple (e.g. "34x ROI vs $99/mo Plan")
  │      ├─► Job Value Calibration Slider ($500 - $2,500)
  │      └─► Breakdown by Lead Source (Voice AI vs Web Form vs Missed Call)
  │
  └──► Tab 3: Quick Controls
         ├─► [🟢 Auto-Rescue Active] Master Toggle
         ├─► Contractor Cell Phone for SMS Push Alerts
         └─► Voice Receptionist Mode Selector
```

---

## 3. Core Functional Requirements

### 3.1 Rescued Revenue Engine
- Configurable `avg_job_value` (default: \$850).
- Calculates:
  - `rescued_leads_count`: Total leads with status `Followed Up` or `Closed`.
  - `total_rescued_value`: `rescued_leads_count * avg_job_value`.
  - `roi_multiple`: `total_rescued_value / 99.0` (or Pro tier).
- Highlights the metric prominently at the top of the app.

### 3.2 iMessage-Style Conversation Drawer
- Slide-over or clean modal overlay designed for one-handed thumb navigation.
- Shows:
  - Customer contact info + 1-tap `tel:` call button.
  - Context box (Service requested + arrival window).
  - Transcript preview if lead came from Voice AI Receptionist.
  - Chat bubbles (Inbound homeowner messages vs. Outbound AI/Contractor replies).
  - Quick-reply text chips.
  - Message input box with send button that posts to `/api/sms/send`.

### 3.3 3-Tab Contractor Navigation
- Eliminates cognitive clutter.
- Responsive mobile bar pinned at bottom on mobile screens and top on desktop.

---

## 4. API Endpoints & State
- `GET /api/leads`: returns leads with `preferred_window`, `address`, `notes`, `status`, and `source`.
- `POST /api/sms/send`: dispatches direct text reply from contractor to customer.
- `POST /api/settings`: saves `avg_job_value`, `contractor_mobile`, and toggle states.
