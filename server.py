import http.server
import socketserver
import json
import os
import urllib.parse
import sys
import time
import db

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8000

# Initialize SQLite database
db.init_db()

def generate_ai_sms_draft(name, service, notes=""):
    """
    Simulates a lightweight LLM API prompt generation for personalized customer SMS follow-up.
    Formats a warm, professional, high-conversion initial text response.
    """
    first_name = name.split()[0] if name else "there"
    service_clean = service.lower() if service else "service"

    if "plumb" in service_clean or "leak" in service_clean or "drain" in service_clean:
        return f"Hi {first_name}! Thanks for reaching out to Lead Rescue Plumbing regarding '{service}'. We have licensed technicians available. Can we call you now to assist?"
    elif "hvac" in service_clean or "ac" in service_clean or "heat" in service_clean:
        return f"Hi {first_name}! We received your request about your HVAC/AC service ('{service}'). Our senior technician is nearby. What time works best for an inspection today?"
    elif "electr" in service_clean or "wire" in service_clean or "panel" in service_clean:
        return f"Hi {first_name}! Thanks for contacting us about your electrical service request ('{service}'). We offer free estimates! Would you prefer a morning or afternoon appointment?"
    elif "roof" in service_clean or "gutter" in service_clean:
        return f"Hi {first_name}! Thanks for inquiring about roofing/gutters for '{service}'. We can perform a quick drone inspection tomorrow morning. Would 9:00 AM work?"
    else:
        return f"Hi {first_name}! Thanks for reaching out to us regarding your request for '{service}'. We received your message and would love to help! When is a good time for a quick 2-minute call?"

class LeadRescueRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/leads":
            leads = db.get_all_leads()
            stats = db.get_stats()
            response = {
                "leads": leads,
                "stats": stats,
                "server_time": time.strftime("%H:%M:%S")
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if parsed.path == "/api/auth/login":
            username = data.get("username", "")
            password = data.get("password", "")
            if username == "admin" and password == "rescue123" or username == "demo":
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "token": "demo_jwt_session_token_xyz89",
                    "user": {"name": "Apex Plumbing & HVAC", "email": "owner@apexrescue.com"}
                }).encode('utf-8'))
            else:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid credentials. Use demo / rescue123"}).encode('utf-8'))
            return

        elif parsed.path == "/api/webhook/lead":
            name = data.get("name", "Valued Customer")
            phone = data.get("phone", "(555) 000-0000")
            service = data.get("service", "General Service Inspection")
            notes = data.get("notes", "Submitted via lead form.")
            source = data.get("source", "Webhook Form")

            # Generate AI SMS Draft
            ai_sms_draft = generate_ai_sms_draft(name, service, notes)

            # Save to Database
            new_id = db.add_lead(name, phone, service, notes, source, ai_sms_draft, status="New")

            # Automatically simulate SMS dispatch if auto-send requested
            auto_send = data.get("auto_send_sms", True)
            if auto_send:
                db.update_lead_status(new_id, "Followed Up", sms_sent=True)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Lead ingested and initial SMS automated!",
                "lead_id": new_id,
                "ai_sms_draft": ai_sms_draft,
                "status": "Followed Up" if auto_send else "New"
            }).encode('utf-8'))
            return

        elif parsed.path == "/api/ai/draft-sms":
            name = data.get("name", "")
            service = data.get("service", "")
            notes = data.get("notes", "")
            draft = generate_ai_sms_draft(name, service, notes)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "ai_sms_draft": draft}).encode('utf-8'))
            return

        elif parsed.path == "/api/sms/send":
            lead_id = data.get("lead_id")
            message = data.get("message", "")
            
            if lead_id:
                db.update_lead_status(lead_id, "Followed Up", sms_sent=True)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "SMS dispatched via Twilio API Gateway!",
                "timestamp": time.strftime("%H:%M:%S")
            }).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if parsed.path == "/api/lead/status":
            lead_id = data.get("lead_id")
            new_status = data.get("status")
            if lead_id and new_status:
                db.update_lead_status(lead_id, new_status)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "lead_id": lead_id, "new_status": new_status}).encode('utf-8'))
                return

        self.send_response(400)
        self.end_headers()

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
