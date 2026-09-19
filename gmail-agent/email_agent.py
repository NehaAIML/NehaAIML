import os
import sys
import json
import base64
import sqlite3
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field
import ollama

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
DB_PATH = os.path.join(BASE_DIR, 'agent_vault.db')
RECIPIENT_EMAIL = 'nrj112@gmail.com'

class EmailSummary(BaseModel):
    subject: str = Field(description="Normalized subject of the email")
    sender: str = Field(description="Sender name or address")
    one_line_summary: str = Field(description="Exactly one dense, high-signal sentence summarizing the core news or update")
    key_highlights: List[str] = Field(description="Up to 3 high-impact technical or operational takeaways", default=[])

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT,
            subject TEXT,
            sender TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def is_already_processed(message_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM processed_emails WHERE message_id = ?', (message_id,))
    res = cur.fetchone()
    conn.close()
    return res is not None

def record_processed_email(message_id: str, thread_id: str, subject: str, sender: str, summary: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT OR IGNORE INTO processed_emails (message_id, thread_id, subject, sender, summary)
        VALUES (?, ?, ?, ?, ?)
    ''', (message_id, thread_id, subject, sender, summary))
    conn.commit()
    conn.close()

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def extract_body(payload) -> str:
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                data = part['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                res = extract_body(part)
                if res:
                    return res
    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return body

def analyze_with_ollama(subject, sender, body):
    import time
    import json
    client = ollama.Client(timeout=120)

    prompt = f"""You are an executive email assistant.
Analyze this email and return a JSON object matching this exact structure:
{{
  "subject": "{subject}",
  "sender": "{sender}",
  "one_line_summary": "1-2 sentence executive summary of the content",
  "action_items": ["Action item 1", "Action item 2"],
  "urgency": "High"
}}

Rules:
- "urgency" must be one of: "High", "Medium", "Low"
- Output only valid JSON. Do not include markdown codeblocks, metadata, or explanations.

Email Subject: {subject}
Sender: {sender}
Body:
{body[:2500]}
"""

    for attempt in range(3):
        try:
            response = client.chat(
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": "You are a concise executive assistant. Output valid JSON only, without markdown wrappers or schema definitions."},
                    {"role": "user", "content": prompt}
                ],
                format="json"
            )
            raw = response['message']['content'].strip()
            if raw.startswith("```"):
                raw = raw.replace("```json", "").replace("```", "").strip()

            data = json.loads(raw)
            if "properties" in data:
                data = {
                    "subject": subject,
                    "sender": sender,
                    "one_line_summary": subject,
                    "action_items": [],
                    "urgency": "Medium"
                }

            data.setdefault("subject", subject)
            data.setdefault("sender", sender)
            data.setdefault("one_line_summary", "No summary provided.")
            data.setdefault("action_items", [])
            data.setdefault("urgency", "Medium")

            return EmailSummary.model_validate(data)
        except Exception as e:
            if attempt < 2:
                time.sleep(4)
                continue
            return EmailSummary(
                subject=subject,
                sender=sender,
                one_line_summary=f"Automated digest fallback: {subject}",
                action_items=[],
                urgency="Medium"
            )

def send_daily_briefing(service, summaries: List[EmailSummary]):
    if not summaries:
        print("[*] No summaries to send today.")
        return

    date_str = datetime.now().strftime("%A, %B %d, %Y")
    body_lines = [
        f"Good morning Neha,\n",
        f"Here is your daily executive email briefing for {date_str}.\n",
        "=" * 50,
        ""
    ]

    for idx, s in enumerate(summaries, 1):
        body_lines.append(f"{idx}. {s.subject}")
        body_lines.append(f"   From: {s.sender}")
        body_lines.append(f"   Summary: {s.one_line_summary}")
        if s.key_highlights:
            body_lines.append("   Key Highlights:")
            for h in s.key_highlights:
                body_lines.append(f"     * {h}")
        body_lines.append("-" * 50)
        body_lines.append("")

    message = MIMEText("\n".join(body_lines))
    message['to'] = RECIPIENT_EMAIL
    message['from'] = RECIPIENT_EMAIL
    message['subject'] = f"Daily Executive Email Digest - {date_str}"
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"[✓] Daily briefing successfully emailed to {RECIPIENT_EMAIL}")

def run_daily_agent():
    init_db()
    service = get_gmail_service()
    
    # Query unread emails received in the last 24 hours from Primary inbox
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    query = f"in:inbox category:primary -subject:\"Daily Executive Email Digest\" after:{yesterday}"
    print(f"[*] Fetching emails with query: '{query}'...")
    
    results = service.users().messages().list(userId='me', q=query, maxResults=25).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("[+] No primary emails found for the past 24 hours.")
        return

    summaries = []
    for msg_meta in messages:
        msg_id = msg_meta['id']
        if is_already_processed(msg_id):
            continue

        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(Unknown Sender)')
        body = extract_body(msg.get('payload', {}))
        
        print(f"[*] Processing: {subject[:50]}...")
        summary = analyze_with_ollama(subject, sender, body)
        summaries.append(summary)
        
        record_processed_email(msg_id, msg.get('threadId', ''), subject, sender, summary.one_line_summary)

    if summaries:
        send_daily_briefing(service, summaries)
    else:
        print("[+] All emails for the day were already summarized.")

if __name__ == '__main__':
    run_daily_agent()
