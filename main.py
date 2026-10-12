"""
=============================================================
 AI AGENT UMKM — FASTAPI VERSION
=============================================================
 Jalankan lokal:
   uvicorn main:app --host 0.0.0.0 --port 5000 --reload
=============================================================
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from engines import AIAgent

# ==================== LOAD ENV ====================
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+17372508034")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None


# ==================== AI AGENT GLOBAL ====================
agent: AIAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    print("=" * 55)
    print("  AI AGENT UMKM — FASTAPI")
    print("=" * 55)
    print(f"  Twilio Number: {TWILIO_WHATSAPP_NUMBER}")
    print(f"  SID loaded: {'OK' if TWILIO_ACCOUNT_SID else 'MISSING'}")
    print(f"  Token loaded: {'OK' if TWILIO_AUTH_TOKEN else 'MISSING'}")
    print("=" * 55)
    agent = AIAgent()
    print("  AI Agent initialized")
    print(f"  Produk terdaftar: {list(agent.data.produk.keys())}")
    print("=" * 55)
    yield
    print("\n Server shutting down...")


# ==================== APP INIT ====================
app = FastAPI(
    title="AI Agent UMKM",
    description="Bot WhatsApp untuk UMKM dengan NLP, Recommendation, dan Forecasting",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MODELS ====================
class KirimRequest(BaseModel):
    to: str
    body: str


# ==================== ENDPOINTS ====================
@app.get("/")
async def index():
    return {
        "status": "AI Agent UMKM aktif",
        "version": "2.0.0",
        "webhook": "/whatsapp",
        "docs": "/docs",
        "produk": list(agent.data.produk.keys()) if agent else [],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(default=""),
    To: str = Form(default=""),
):
    incoming_msg = Body.strip()
    sender = From

    print(f"\n Pesan masuk dari {sender}: {incoming_msg}")

    if not incoming_msg:
        balasan = "Halo! Kirim pesan untuk mulai chat ya"
    else:
        balasan = agent.handle_chat(incoming_msg)

    print(f" Balasan AI: {balasan}\n")

    resp = MessagingResponse()
    resp.message(balasan)
    return PlainTextResponse(
        content=str(resp),
        media_type="application/xml",
    )


@app.post("/kirim")
async def kirim_pesan(req: KirimRequest):
    if not twilio_client:
        raise HTTPException(status_code=500, detail="Twilio client not configured")

    try:
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{req.to}",
            body=req.body,
        )
        return {"sid": message.sid, "status": "terkirim"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info",
    )

