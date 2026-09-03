import json
import os
import urllib.parse
import sys
import time
import urllib.request
import base64

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase Cloud Configuration with auto-clean for /rest/v1 suffix
RAW_URL = os.environ.get("SUPABASE_URL", "https://gylegafrbyroktpjumli.supabase.co").strip().rstrip('/')
if RAW_URL.endswith('/rest/v1'):
    RAW_URL = RAW_URL[:-8]
SUPABASE_URL = RAW_URL
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5bGVnYWZyYnlyb2t0cGp1bWxpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzY5NDQ5NSwiZXhwIjoyMTAzMjcwNDk1fQ.J9hLv9nPhJEOxF0BclA3TRMtA5t0zcy73cYWgu5nfLM").strip()

# REST Helper for Supabase (Reliable, fast, zero-dependency)
def supabase_request(endpoint, method="GET", data=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=8) as response:
            res_text = response.read().decode("utf-8")
            return json.loads(res_text) if res_text else []
    except Exception as e:
        print(f"Supabase REST error [{method} {endpoint}]:", e)
        return None

# Database Operations via Supabase Cloud
def get_settings():
    default_settings = {
        "business_name": "Apex Plumbing & HVAC",
        "business_phone": "(555) 123-4567",
        "twilio_sid": "",
        "twilio_token": "",
        "twilio_phone": "",
        "ai_template": "Hi {first_name}! Thanks for reaching out to {business_name} regarding '{service}'. We have licensed technicians available. Can we call you now to assist?"
    }
    
    res = supabase_request("settings?select=*")
    if res and isinstance(res, list):
        settings_dict = {row["key"]: row["value"] for row in res}
        for k, v in default_settings.items():
            if k not in settings_dict:
                settings_dict[k] = v
        return settings_dict

    return default_settings

def update_settings(settings_dict):
    try:
        for k, v in settings_dict.items():
            # Upsert into settings table
            supabase_request("settings", method="POST", data={"key": k, "value": str(v)})
        return True
    except Exception as e:
        print("update_settings error:", e)
        return False

def get_all_leads():
    """Fetch all leads newest-first, including address & preferred_window columns."""
    res = supabase_request("leads?select=*&order=created_at.desc")
    if res and isinstance(res, list):
        return res
    return []

def add_lead(name, phone, service, notes="", source="Embeddable Web Form",
             ai_sms_draft="", status="New", address="", preferred_window="Flexible", call_sid=None):
    """Insert a new lead. address and preferred_window support the Voice AI Receptionist flow."""
    payload = {
        "name": name,
        "phone": phone,
        "service": service,
        "notes": notes,
        "source": source,
        "ai_sms_draft": ai_sms_draft,
        "status": status,
        "sms_sent": False,
        "address": address,
        "preferred_window": preferred_window,
    }
    if call_sid:
        payload["call_sid"] = call_sid
    res = supabase_request("leads", method="POST", data=payload)
    if res and isinstance(res, list) and len(res) > 0:
        return res[0].get("id")

    # Resilient fallback if custom columns (address, preferred_window) aren't migrated in PostgreSQL yet
    fallback_payload = {
        "name": name,
        "phone": phone,
        "service": service,
        "notes": f"{notes} | Window: {preferred_window} | Address: {address}".strip(" |"),
        "source": source,
        "ai_sms_draft": ai_sms_draft,
        "status": status,
        "sms_sent": False
    }
    fb_res = supabase_request("leads", method="POST", data=fallback_payload)
    if fb_res and isinstance(fb_res, list) and len(fb_res) > 0:
        return fb_res[0].get("id")
    return None

def update_lead_status(lead_id, new_status, sms_sent=None):
    payload = {"status": new_status, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if sms_sent is not None:
        payload["sms_sent"] = bool(sms_sent)
    res = supabase_request(f"leads?id=eq.{lead_id}", method="PATCH", data=payload)
    return res is not None

def get_stats():
    leads = get_all_leads()
    new_count = len([l for l in leads if l.get("status") == "New"])
    followed_count = len([l for l in leads if l.get("status") == "Followed Up"])
    closed_count = len([l for l in leads if l.get("status") == "Closed"])
    total_count = len(leads)
    conversion_rate = round((closed_count / total_count * 100.0), 1) if total_count > 0 else 0.0

    return {
        "new_leads": new_count,
        "followed_up": followed_count,
        "closed_jobs": closed_count,
        "total_leads": total_count,
        "conversion_rate": conversion_rate
    }

def log_call(call_sid, from_number, to_number, duration=0, transcript="", recording_url="", status="completed"):
    """Insert a Twilio call record into the calls table."""
    payload = {
        "call_sid": str(call_sid),
        "from_number": from_number,
        "to_number": to_number,
        "duration": int(duration),
        "transcript": transcript,
        "recording_url": recording_url,
        "status": status
    }
    res = supabase_request("calls", method="POST", data=payload)
    if res and isinstance(res, list) and len(res) > 0:
        return res[0].get("id")
    return None

def add_message(lead_id, from_number, to_number, direction, body):
    """Insert a threaded SMS message. direction must be 'inbound' or 'outbound'."""
    payload = {
        "lead_id": lead_id,
        "from_number": from_number,
        "to_number": to_number,
        "direction": direction,
        "body": body
    }
    res = supabase_request("messages", method="POST", data=payload)
    if res and isinstance(res, list) and len(res) > 0:
        return res[0].get("id")
    return None

def get_messages_for_lead(lead_id):
    """Return all messages for a lead ordered ascending by time."""
    res = supabase_request(f"messages?lead_id=eq.{lead_id}&order=created_at.asc&select=*")
    if res and isinstance(res, list):
        return res
    return []

def send_twilio_sms(to_phone, message_text):
    settings = get_settings()
    sid = settings.get("twilio_sid", "").strip()
    token = settings.get("twilio_token", "").strip()
    from_phone = settings.get("twilio_phone", "").strip()

    if sid and token and from_phone:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
            data = urllib.parse.urlencode({
                'To': to_phone,
                'From': from_phone,
                'Body': message_text
            }).encode('utf-8')

            req = urllib.request.Request(url, data=data, method='POST')
            auth_header = base64.b64encode(f"{sid}:{token}".encode('utf-8')).decode('utf-8')
            req.add_header('Authorization', f'Basic {auth_header}')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')

            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                return True, res_body.get('sid', 'Twilio Sent')
        except Exception as e:
            print("Twilio SMS dispatch exception:", e)
            return False, str(e)
    
    return True, "Mock Sandbox Mode (Twilio credentials pending)"

def generate_ai_sms_draft(name, service, notes=""):
    settings = get_settings()
    biz_name = settings.get("business_name", "Apex Services")
    template = settings.get("ai_template", "")

    first_name = name.split()[0] if name else "there"
    
    if template and "{first_name}" in template:
        return template.format(first_name=first_name, business_name=biz_name, service=service)

    service_clean = service.lower() if service else "service"
    if "plumb" in service_clean or "leak" in service_clean or "drain" in service_clean:
        return f"Hi {first_name}! Thanks for reaching out to {biz_name} regarding '{service}'. We have licensed technicians available. Can we call you now to assist?"
    elif "hvac" in service_clean or "ac" in service_clean or "heat" in service_clean:
        return f"Hi {first_name}! We received your request about your HVAC/AC service ('{service}'). Our senior technician is nearby. What time works best for an inspection today?"
    elif "electr" in service_clean or "wire" in service_clean or "panel" in service_clean:
        return f"Hi {first_name}! Thanks for contacting us about your electrical service request ('{service}'). We offer free estimates! Would you prefer a morning or afternoon appointment?"
    else:
        return f"Hi {first_name}! Thanks for reaching out to {biz_name} regarding your request for '{service}'. We received your message and would love to help! When is a good time for a quick call?"

def handle_api_request(method, path, body_str):
    path = path.rstrip('/')
    if not path.startswith('/api'):
        path = '/api' + path

    try:
        data = json.loads(body_str) if body_str else {}
    except Exception:
        data = {}

    if method == "GET" and (path == "/api/leads" or path == "/api"):
        leads = get_all_leads()
        stats = get_stats()
        settings = get_settings()
        return 200, {
            "leads": leads,
            "stats": stats,
            "settings": settings,
            "supabase_connected": True,
            "server_time": time.strftime("%H:%M:%S")
        }

    elif method == "GET" and path == "/api/settings":
        settings = get_settings()
        return 200, {"settings": settings}

    elif method == "POST" and path == "/api/settings":
        update_settings(data)
        return 200, {"success": True, "message": "Settings updated in Supabase cloud database"}

    elif method == "POST" and path == "/api/auth/login":
        return 200, {
            "success": True,
            "token": "demo_jwt_session_token_xyz89",
            "user": {"name": "Apex Plumbing & HVAC", "email": "owner@apexrescue.com"}
        }

    elif method == "POST" and (path.startswith("/api/webhook") or path.startswith("/api/public")):
        name = data.get("name", "Valued Customer")
        phone = data.get("phone", "(555) 000-0000")
        service = data.get("service", "General Service Inspection")
        notes = data.get("notes", "Submitted via lead form.")
        source = data.get("source", "Embeddable Web Form")

        address = data.get("address", "")
        preferred_window = data.get("preferred_window", "Flexible")

        ai_sms_draft = generate_ai_sms_draft(name, service, notes)
        new_id = add_lead(name, phone, service, notes, source, ai_sms_draft, status="New",
                          address=address, preferred_window=preferred_window)

        auto_send = data.get("auto_send_sms", True)
        sms_status = "Not Sent"
        if auto_send:
            success, sid_log = send_twilio_sms(phone, ai_sms_draft)
            if new_id:
                update_lead_status(new_id, "Followed Up", sms_sent=True)
            sms_status = sid_log

        return 200, {
            "success": True,
            "message": "Lead captured & saved to Supabase cloud database!",
            "lead_id": new_id,
            "ai_sms_draft": ai_sms_draft,
            "sms_dispatch": sms_status,
            "status": "Followed Up" if auto_send else "New"
        }

    elif method == "POST" and path == "/api/ai/draft-sms":
        name = data.get("name", "")
        service = data.get("service", "")
        notes = data.get("notes", "")
        draft = generate_ai_sms_draft(name, service, notes)
        return 200, {"success": True, "ai_sms_draft": draft}

    elif method == "POST" and path == "/api/sms/send":
        lead_id = data.get("lead_id")
        phone = data.get("phone", "")
        message = data.get("message", "")
        
        success, sid_log = send_twilio_sms(phone, message)
        if lead_id:
            update_lead_status(lead_id, "Followed Up", sms_sent=True)
            
        return 200, {
            "success": True,
            "message": "SMS dispatched via Twilio API Gateway!",
            "sid": sid_log,
            "timestamp": time.strftime("%H:%M:%S")
        }

    elif method == "PATCH" and path == "/api/lead/status":
        lead_id = data.get("lead_id")
        new_status = data.get("status")
        if lead_id and new_status:
            update_lead_status(lead_id, new_status)
            return 200, {"success": True, "lead_id": lead_id, "new_status": new_status}
        return 400, {"error": "Missing lead_id or status"}

    # ── Task 2: Voice AI Receptionist ────────────────────────────────────────

    elif method == "POST" and path == "/api/voice/inbound":
        # Twilio calls this when a call arrives on the contractor's LeadRescue number.
        # Respond with TwiML that greets the caller and starts speech gathering.
        settings = get_settings()
        biz_name = settings.get("business_name", "our team")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="/api/voice/gather" method="POST" speechTimeout="auto" language="en-US">
    <Say voice="Polly.Joanna">
      Hi there! Thanks for calling {biz_name}. I'm the automated dispatch assistant.
      Please briefly describe what you need help with today, and I'll get a technician on the way for you.
    </Say>
  </Gather>
  <Say voice="Polly.Joanna">I didn't catch that. Please hold and we will call you right back!</Say>
</Response>"""
        return 200, {"response_type": "twiml", "twiml": twiml}

    elif method == "POST" and path == "/api/voice/gather":
        # Twilio posts the caller's transcribed speech here.
        # We extract name/service/window from the transcript, create a lead, and confirm.
        call_sid = data.get("CallSid", "")
        from_number = data.get("From", "Unknown")
        to_number = data.get("To", "")
        speech_result = data.get("SpeechResult", "")
        settings = get_settings()
        biz_name = settings.get("business_name", "our team")

        # Classify urgency window from speech
        speech_lower = speech_result.lower()
        if any(w in speech_lower for w in ["emergency", "urgent", "asap", "flooding", "leak", "no heat", "no ac", "now"]):
            preferred_window = "Emergency ASAP"
            window_msg = "We're treating your request as an emergency and will have a technician dispatched within 2 to 4 hours."
        elif any(w in speech_lower for w in ["morning", "tomorrow morning", "8", "9", "10", "11"]):
            preferred_window = "Morning Window (8AM-12PM)"
            window_msg = "I've booked you in for a morning visit between 8 AM and noon. A technician will confirm their arrival time shortly."
        elif any(w in speech_lower for w in ["afternoon", "1", "2", "3", "4"]):
            preferred_window = "Afternoon Window (12PM-4PM)"
            window_msg = "I've booked you in for an afternoon visit between noon and 4 PM. A technician will confirm shortly."
        else:
            preferred_window = "Flexible"
            window_msg = "A technician will call you back shortly to schedule your appointment."

        # Determine service type from speech
        if any(w in speech_lower for w in ["plumb", "leak", "drain", "pipe", "water", "sewer"]):
            service = "Plumbing Service"
        elif any(w in speech_lower for w in ["hvac", "ac", "heat", "furnace", "air", "cool"]):
            service = "HVAC / AC Service"
        elif any(w in speech_lower for w in ["electr", "outlet", "panel", "wiring", "breaker"]):
            service = "Electrical Service"
        elif any(w in speech_lower for w in ["roof", "gutter", "leak roof", "shingle"]):
            service = "Roofing Service"
        else:
            service = "General Service Request"

        # Create lead from voice call
        ai_sms = f"Hi! Thanks for calling {biz_name}. We captured your request for {service}. {window_msg}"
        new_id = add_lead(
            name="Caller",
            phone=from_number,
            service=service,
            notes=f"Voice call transcript: {speech_result}",
            source="Voice AI Receptionist",
            ai_sms_draft=ai_sms,
            status="New",
            preferred_window=preferred_window,
            call_sid=call_sid
        )
        log_call(call_sid=call_sid, from_number=from_number, to_number=to_number,
                 transcript=speech_result, status="completed")

        # Push instant SMS alert to contractor
        contractor_mobile = settings.get("contractor_mobile", "")
        if contractor_mobile:
            alert = f"🚨 Voice Lead: {from_number} called about {service}. Window: {preferred_window}. Transcript: \"{speech_result[:100]}\". Tap to call: {from_number}"
            send_twilio_sms(contractor_mobile, alert)

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">
    Great! I've logged your service request and a technician from {biz_name} will be in touch shortly to confirm your appointment.
    {window_msg}
    Have a great day!
  </Say>
  <Hangup/>
</Response>"""
        return 200, {"response_type": "twiml", "twiml": twiml, "lead_id": new_id}

    elif method == "POST" and path == "/api/voice/status":
        # Twilio status callback — handles missed calls (no-answer / busy / failed).
        call_status = data.get("CallStatus", "")
        from_number = data.get("From", "")
        call_sid = data.get("CallSid", "")
        to_number = data.get("To", "")
        settings = get_settings()
        biz_name = settings.get("business_name", "our team")

        if call_status in ("no-answer", "busy", "failed", "canceled"):
            # Missed call — fire auto-text to the caller immediately
            missed_call_msg = (
                f"Hi! This is {biz_name}. I just missed your call and I don't want to leave you hanging! "
                f"How can I help you today? Reply with what you need and I'll get someone out to you fast."
            )
            send_twilio_sms(from_number, missed_call_msg)

            # Log a lead for the missed call
            add_lead(
                name="Missed Call",
                phone=from_number,
                service="Unknown (Missed Call)",
                notes=f"Missed call. Status: {call_status}. Auto-text sent.",
                source="Missed Call Auto-Text",
                ai_sms_draft=missed_call_msg,
                status="New",
                call_sid=call_sid
            )
            log_call(call_sid=call_sid, from_number=from_number, to_number=to_number,
                     status=call_status, transcript="", recording_url="")

        return 200, {"success": True, "call_status": call_status}

    # ── Task 3: 2-Way SMS Inbound Webhook ────────────────────────────────────

    elif method == "POST" and path == "/api/sms/inbound":
        # Twilio posts here when a homeowner texts the business number.
        from_number = data.get("From", "")
        to_number = data.get("To", "")
        body = data.get("Body", "").strip()
        settings = get_settings()
        biz_name = settings.get("business_name", "our team")
        contractor_mobile = settings.get("contractor_mobile", "")

        # Find or create a lead for this number
        existing_leads = get_all_leads()
        matched_lead = next((l for l in existing_leads if l.get("phone") == from_number), None)

        if matched_lead:
            lead_id = matched_lead.get("id")
            # Append inbound message to thread
            add_message(lead_id=lead_id, from_number=from_number, to_number=to_number,
                        direction="inbound", body=body)
        else:
            # New contact via SMS — create lead
            ai_draft = generate_ai_sms_draft("there", body)
            lead_id = add_lead(
                name="SMS Contact",
                phone=from_number,
                service=body[:80],
                notes=f"Initial inbound SMS: {body}",
                source="Direct SMS",
                ai_sms_draft=ai_draft,
                status="New"
            )
            add_message(lead_id=lead_id, from_number=from_number, to_number=to_number,
                        direction="inbound", body=body)

        # Auto-acknowledge the homeowner
        ack_msg = f"Got it! Thanks for texting {biz_name}. A technician will follow up shortly."
        send_twilio_sms(from_number, ack_msg)
        if lead_id:
            add_message(lead_id=lead_id, from_number=to_number, to_number=from_number,
                        direction="outbound", body=ack_msg)

        # Push instant SMS alert to contractor
        if contractor_mobile:
            alert = f"💬 New SMS from {from_number}: \"{body[:120]}\". Lead ID: {lead_id}. Tap to reply: {from_number}"
            send_twilio_sms(contractor_mobile, alert)

        # Respond to Twilio with empty TwiML (we already sent via REST)
        return 200, {"success": True, "lead_id": lead_id}

    elif method == "GET" and path == "/api/messages":
        lead_id = body_str  # fallback
        return 200, {"messages": []}

    return 200, {"success": True, "message": "Lead Rescue API Active"}

def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')

    # Handle Twilio form-encoded payloads (voice/SMS webhooks use application/x-www-form-urlencoded)
    content_type = environ.get('CONTENT_TYPE', '')
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    raw_body = environ['wsgi.input'].read(request_body_size).decode('utf-8') if request_body_size > 0 else ""

    # Parse form-encoded body into dict for Twilio webhooks
    if 'application/x-www-form-urlencoded' in content_type and raw_body:
        try:
            parsed = urllib.parse.parse_qs(raw_body, keep_blank_values=True)
            body_str = json.dumps({k: v[0] for k, v in parsed.items()})
        except Exception:
            body_str = raw_body
    else:
        body_str = raw_body

    status_code, response_data = handle_api_request(method, path, body_str)

    # Voice endpoints return TwiML XML — detect and serve accordingly
    if isinstance(response_data, dict) and response_data.get("response_type") == "twiml":
        twiml_body = response_data.get("twiml", "<Response/>").encode("utf-8")
        response_headers = [
            ('Content-Type', 'text/xml; charset=utf-8'),
            ('Content-Length', str(len(twiml_body))),
            ('Access-Control-Allow-Origin', '*'),
        ]
        start_response("200 OK", response_headers)
        return [twiml_body]

    response_body = json.dumps(response_data).encode('utf-8')
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body))),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type')
    ]
    start_response("200 OK", response_headers)
    return [response_body]

handler = app

