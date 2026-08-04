import sqlite3
import os
import json
import time

# Use /tmp on Vercel serverless or local directory
if os.path.exists('/tmp') and os.access('/tmp', os.W_OK):
    DB_FILE = os.path.join('/tmp', 'leads_database.sqlite')
else:
    DB_FILE = 'leads_database.sqlite'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            notes TEXT,
            source TEXT DEFAULT 'Website Form',
            status TEXT DEFAULT 'New',
            ai_sms_draft TEXT,
            sms_sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_leads = [
            {
                "name": "Sarah Jenkins",
                "phone": "(555) 234-5678",
                "service": "Emergency Plumbing - Water Heater Leak",
                "notes": "Water heater leaking in garage, need urgent quote.",
                "source": "Google Local Ad",
                "status": "New",
                "ai_sms_draft": "Hi Sarah! Thanks for reaching out to Apex Services regarding your water heater leak. We can have a licensed technician at your property within 45 mins. Are you available for a quick call?"
            },
            {
                "name": "Marcus Vance",
                "phone": "(555) 876-5432",
                "service": "HVAC AC Repair",
                "notes": "AC unit blowing warm air, temp is 88 degrees inside.",
                "source": "Website Missed Call",
                "status": "Followed Up",
                "ai_sms_draft": "Hi Marcus! We received your request about your AC blowing warm air. Our senior technician Tom is nearby. Would 2:30 PM work for an inspection?",
                "sms_sent": 1
            },
            {
                "name": "Elena Rodriguez",
                "phone": "(555) 432-1098",
                "service": "Electrical Panel Upgrade",
                "notes": "Looking to upgrade 100A panel to 200A for EV charger installation.",
                "source": "Yelp Direct Form",
                "status": "Closed",
                "ai_sms_draft": "Hi Elena! Thanks for contacting us about your 200A panel upgrade for your EV charger. We've scheduled your estimate for Friday at 10 AM!",
                "sms_sent": 1
            }
        ]
        for lead in seed_leads:
            cursor.execute('''
                INSERT INTO leads (name, phone, service, notes, source, status, ai_sms_draft, sms_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (lead["name"], lead["phone"], lead["service"], lead["notes"], lead.get("source", "Website"), lead["status"], lead["ai_sms_draft"], lead.get("sms_sent", 0)))
        conn.commit()
    conn.close()

def get_all_leads():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return leads

def add_lead(name, phone, service, notes="", source="Webhook Form", ai_sms_draft="", status="New"):
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leads (name, phone, service, notes, source, status, ai_sms_draft)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, phone, service, notes, source, status, ai_sms_draft))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_lead_status(lead_id, new_status, sms_sent=None):
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    if sms_sent is not None:
        cursor.execute('''
            UPDATE leads SET status = ?, sms_sent = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (new_status, 1 if sms_sent else 0, lead_id))
    else:
        cursor.execute('''
            UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (new_status, lead_id))
    conn.commit()
    conn.close()

def get_stats():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'New'")
    new_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Followed Up'")
    followed_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Closed'")
    closed_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_count = cursor.fetchone()[0]
    conn.close()

    conversion_rate = round((closed_count / total_count * 100.0), 1) if total_count > 0 else 0.0

    return {
        "new_leads": new_count,
        "followed_up": followed_count,
        "closed_jobs": closed_count,
        "total_leads": total_count,
        "conversion_rate": conversion_rate
    }
