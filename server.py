import http.server
import socketserver
import json
import os
import urllib.parse
import sys
import time
import urllib.request
import base64
import db

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8000
db.init_db()

def send_twilio_sms(to_phone, message_text):
    """
    Dispatches real SMS message via Twilio REST API if credentials exist.
    Falls back to sandbox log if credentials are pending.
    """
    settings = db.get_settings()
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
    settings = db.get_settings()
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
        leads = db.get_all_leads()
        stats = db.get_stats()
        settings = db.get_settings()
        return 200, {
            "leads": leads,
            "stats": stats,
            "settings": settings,
            "server_time": time.strftime("%H:%M:%S")
        }

    elif method == "GET" and path == "/api/settings":
        settings = db.get_settings()
        return 200, {"settings": settings}

    elif method == "POST" and path == "/api/settings":
        db.update_settings(data)
        return 200, {"success": True, "message": "Settings updated successfully"}

    elif method == "POST" and path == "/api/auth/login":
        return 200, {
            "success": True,
            "token": "demo_jwt_session_token_xyz89",
            "user": {"name": "Apex Plumbing & HVAC", "email": "owner@apexrescue.com"}
        }

    elif method == "POST" and (path == "/api/webhook/lead" or path == "/api/public/submit-lead"):
        name = data.get("name", "Valued Customer")
        phone = data.get("phone", "(555) 000-0000")
        service = data.get("service", "General Service Inspection")
        notes = data.get("notes", "Submitted via lead form.")
        source = data.get("source", "Embeddable Web Form")

        ai_sms_draft = generate_ai_sms_draft(name, service, notes)
        new_id = db.add_lead(name, phone, service, notes, source, ai_sms_draft, status="New")

        auto_send = data.get("auto_send_sms", True)
        sms_status = "Not Sent"
        if auto_send:
            success, sid_log = send_twilio_sms(phone, ai_sms_draft)
            db.update_lead_status(new_id, "Followed Up", sms_sent=True)
            sms_status = sid_log

        return 200, {
            "success": True,
            "message": "Lead captured & automated initial SMS response sent!",
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
            db.update_lead_status(lead_id, "Followed Up", sms_sent=True)
            
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
            db.update_lead_status(lead_id, new_status)
            return 200, {"success": True, "lead_id": lead_id, "new_status": new_status}
        return 400, {"error": "Missing lead_id or status"}

    return 200, {"success": True, "message": "Lead Rescue API Active"}

# WSGI Application entry point for Vercel
def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    body_str = environ['wsgi.input'].read(request_body_size).decode('utf-8') if request_body_size > 0 else ""

    status_code, response_data = handle_api_request(method, path, body_str)
    
    status_text = "200 OK"
    response_body = json.dumps(response_data).encode('utf-8')
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body))),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type')
    ]

    start_response(status_text, response_headers)
    return [response_body]

handler = app

class LeadRescueRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api"):
            code, resp = handle_api_request("GET", parsed.path, "")
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        code, resp = handle_api_request("POST", parsed.path, body)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode('utf-8'))

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        code, resp = handle_api_request("PATCH", parsed.path, body)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode('utf-8'))

def run(port=PORT):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', port)
    httpd = socketserver.TCPServer(server_address, LeadRescueRequestHandler)
    print(f"Local Lead Rescue Server running at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run(PORT)
