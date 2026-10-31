"""
Real Estate Lead Processing System
FastAPI + SQLite + Telegram + SMTP
"""
import os
import json
import time
import sqlite3
import smtplib
import requests
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Load environment variables
BOT_TOKEN = os.getenv("HERMES_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Initialize database
def init_db():
    conn = sqlite3.connect("/opt/data/my_ai_automation/leads_step11.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_lead(name, email, phone, message, interest=""):
    conn = sqlite3.connect("/opt/data/my_ai_automation/leads_step11.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO leads (user_id, name, email, phone, message, interest)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (0, name, email, phone, message, interest))
    conn.commit()
    conn.close()

# Telegram notification helper
def send_telegram_notification(name, email, phone, message, interest=""):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        text = (
            f"🆕 New Lead Received!\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Phone: {phone}\n"
            f"Interest: {interest or '—'}\n"
            f"Message: {message}\n\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Telegram notification error: {e}")

# SMTP email helper
def send_email(to_email, name, subject, body):
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        return  # Skip if env vars not set
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send error: {e}")

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load initial DB
init_db()

class LeadPayload(BaseModel):
    name: str
    email: str
    phone: str
    message: str

@app.post("/api/submit")
async def submit_lead(request: Request):
    # Support both JSON body AND standard HTML Form (multipart/form-data / url-encoded)
    content_type = request.headers.get("content-type", "")
    name = email = phone = message = interest = ""
    try:
        if "application/json" in content_type:
            payload = await request.json()
            name = payload.get("name", "")
            email = payload.get("email", "")
            phone = payload.get("phone", "")
            interest = payload.get("interest", "")
            message = payload.get("message", "")
        else:
            form_data = await request.form()
            name = form_data.get("name", "")
            email = form_data.get("email", "")
            phone = form_data.get("phone", "")
            interest = form_data.get("interest", "")
            message = form_data.get("message", "")
    except Exception as e:
        return JSONResponse({"status": "error", "message": "Invalid input format: " + str(e)}, status_code=400)

    # Save to database
    save_lead(name, email, phone, message, interest)
    
    # Send Telegram notification
    send_telegram_notification(name, email, phone, message, interest)

    # Send automated email response (optional)
    if SMTP_USER and SMTP_PASS:
        email_body = (
            f"Dear {name},\n\n"
            f"Thank you for your inquiry! We have received your message and will contact you soon.\n\n"
            f"Details received:\n"
            f"- Name: {name}\n"
            f"- Email: {email}\n"
            f"- Phone: {phone}\n"
            f"- Interest: {interest or '—'}\n"
            f"- Message: {message}\n\n"
            f"Best regards,\n"
            f"Hermes Real Estate Team"
        )
        send_email(email, name, "Welcome to Hermes Real Estate", email_body)

    return {"status": "success", "message": "Lead received successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "running", "version": "1.0"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Real Estate Lead Processing API", "docs": "/docs"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)