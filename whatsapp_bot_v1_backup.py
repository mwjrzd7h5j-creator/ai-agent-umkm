"""
=============================================================
 AI AGENT UMKM — WHATSAPP BOT DENGAN TWILIO
 Studi Kasus 6: AI untuk UMKM
=============================================================
 Arsitektur:
   WhatsApp -> Twilio Webhook -> Flask -> AI Agent -> Twilio API -> WhatsApp
=============================================================
"""

import os
import re
from datetime import datetime
from collections import Counter, defaultdict

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client


# ==================== KONFIGURASI ====================
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)


# ==================== LAPISAN 1: DATA STORE ====================
class DataStore:
    """Menyimpan semua data: produk, transaksi, feedback."""

    def __init__(self):
        self.produk = {
            "kopi susu":   {"harga": 18000, "stok": 45},
            "kopi hitam":  {"harga": 12000, "stok": 30},
            "es teh":      {"harga": 8000,  "stok": 50},
            "roti bakar":  {"harga": 15000, "stok": 20},
            "nasi goreng": {"harga": 20000, "stok": 15},
        }
        self.transaksi = [
            (1, "kopi susu", 40), (1, "es teh", 25), (1, "roti bakar", 10),
            (2, "kopi susu", 42), (2, "es teh", 30), (2, "roti bakar", 12),
            (3, "kopi susu", 38), (3, "es teh", 28), (3, "roti bakar", 8),
            (4, "kopi susu", 45), (4, "es teh", 32), (4, "roti bakar", 15),
            (5, "kopi susu", 50), (5, "es teh", 35), (5, "roti bakar", 18),
            (6, "kopi susu", 65), (6, "es teh", 40), (6, "roti bakar", 25),
            (7, "kopi susu", 30), (7, "es teh", 20), (7, "roti bakar", 7),
        ]

    def cari_produk(self, teks):
        teks_lower = teks.lower()
        for nama in self.produk:
            if nama in teks_lower:
                return nama
        return None

    def total_terjual(self, produk):
        return sum(j for _, p, j in self.transaksi if p == produk)

    def tren_penjualan(self, produk):
        per_hari = defaultdict(int)
        for hari, p, j in self.transaksi:
            if p == produk:
                per_hari[hari] += j
        return [per_hari[h] for h in sorted(per_hari)]


# ==================== LAPISAN 2A: NLP ENGINE ====================
class NLPEngine:
    INTENTS = {
        "sapaan":       [r"\b(halo|hai|hi|assalam|pagi|siang|sore|malam)\b"],
        "tanya_stok":   [r"(masih ada|stok|tersedia|ready|sisa)"],
        "tanya_harga":  [r"(harga|berapa|brp)"],
        "pesan":        [r"(pesan|beli|order|mau|minta|ambil)"],
        "rekomendasi":  [r"(rekomendasi|saran|enaknya|recommend|bagus)"],
        "prediksi":     [r"(prediksi|besok|ramalan|forecast|perkiraan)"],
        "terima_kasih": [r"(makasih|terima kasih|thanks|thx)"],
    }

    def deteksi(self, teks):
        teks_lower = teks.lower()
        for intent, patterns in self.INTENTS.items():
            for pola in patterns:
                if re.search(pola, teks_lower):
                    return intent
        return "tidak_dikenali"

    def ekstrak_jumlah(self, teks):
        match = re.search(r"\b(\d+)\b", teks)
        return int(match.group(1)) if match else 1


# ==================== LAPISAN 2B: RECOMMENDATION ENGINE ====================
class RecommendationEngine:
    def __init__(self, data: DataStore):
        self.data = data

    def produk_terlaris(self):
        counter = Counter()
        for _, p, j in self.data.transaksi:
            counter[p] += j
        return counter.most_common(3)

    def analisis_tren(self, produk):
        harian = self.data.tren_penjualan(produk)
        if len(harian) < 2:
            return 0
        awal, akhir = harian[0], harian[-1]
        return round(((akhir - awal) / awal) * 100, 1)

    def saran_harian(self):
        saran = []
        terlaris = self.produk_terlaris()
        if terlaris:
            nama, total = terlaris[0]
            saran.append(f"Produk terlaris: {nama.upper()} ({total} terjual/minggu)")
        for produk in self.data.produk:
            tren = self.analisis_tren(produk)
            if tren > 20:
                saran.append(f"Tren NAIK: {produk} (+{tren}%) — siapin stok lebih")
            elif tren < -20:
                saran.append(f"Tren TURUN: {produk} ({tren}%) — kurangi stok")
        return saran

    def rekomendasi_untuk_pelanggan(self):
        terlaris = self.produk_terlaris()[0][0]
        return f"Rekomendasi kami: {terlaris} (paling laris minggu ini)"


# ==================== LAPISAN 2C: FORECASTING ENGINE ====================
class ForecastingEngine:
    def __init__(self, data: DataStore):
        self.data = data

    def prediksi_besok(self, produk):
        harian = self.data.tren_penjualan(produk)
        if len(harian) < 3:
            return None
        ma3 = sum(harian[-3:]) / 3
        growth = (harian[-1] - harian[0]) / harian[0]
        prediksi = ma3 * (1 + growth * 0.3)
        return round(prediksi)

    def status_stok(self, produk):
        prediksi = self.prediksi_besok(produk)
        stok = self.data.produk[produk]["stok"]
        if prediksi is None:
            return "Data kurang"
        if stok < prediksi:
            return f"KURANG! Stok {stok} < Prediksi {prediksi}"
        return f"AMAN (Stok {stok}, Prediksi {prediksi})"


# ==================== LAPISAN 3: AI AGENT ====================
class AIAgent:
    def __init__(self):
        self.data = DataStore()
        self.nlp = NLPEngine()
        self.rec = RecommendationEngine(self.data)
        self.fc = ForecastingEngine(self.data)

    def handle_chat(self, teks):
        intent = self.nlp.deteksi(teks)
        produk = self.data.cari_produk(teks)

        if intent == "sapaan":
            return "Halo! Selamat datang di Warung Bu Sari 👋\nAda yang bisa kami bantu?"

        elif intent == "tanya_stok":
            if produk:
                info = self.data.produk[produk]
                return f"{produk.title()} masih ada {info['stok']} pcs ✅"
            return "Produk apa yang mau dicek stoknya, Kak?"

        elif intent == "tanya_harga":
            if produk:
                return f"Harga {produk.title()}: Rp{self.data.produk[produk]['harga']:,}"
            return f"Produk tersedia: {', '.join(self.data.produk.keys())}"

        elif intent == "pesan":
            if produk:
                jumlah = self.nlp.ekstrak_jumlah(teks)
                info = self.data.produk[produk]
                if info["stok"] >= jumlah:
                    total = info["harga"] * jumlah
                    info["stok"] -= jumlah
                    return (f"✅ Pesanan diterima!\n"
                            f"{jumlah}x {produk.title()} = Rp{total:,}\n"
                            f"Silakan bayar via QRIS. Terima kasih!")
                return f"Maaf, stok {produk} hanya {info['stok']} pcs."
            return "Produk apa yang mau dipesan?"

        elif intent == "rekomendasi":
            return self.rec.rekomendasi_untuk_pelanggan()

        elif intent == "prediksi":
            if produk:
                p = self.fc.prediksi_besok(produk)
                return f"Prediksi {produk} besok: ~{p} pcs"
            return "Produk mana yang mau diprediksi?"

        elif intent == "terima_kasih":
            return "Sama-sama, Kak! 🙏 Ditunggu orderan berikutnya."

        return "Maaf, saya belum paham. Coba tanya: 'kopi susu masih ada?'"


# ==================== FLASK WEBHOOK ====================
agent = AIAgent()


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Terima pesan WhatsApp masuk dari Twilio."""
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")

    print(f"\n📩 Pesan masuk dari {sender}: {incoming_msg}")

    # Proses dengan AI Agent
    balasan = agent.handle_chat(incoming_msg)

    print(f"🤖 Balasan AI: {balasan}\n")

    # Kirim balasan via TwiML
    resp = MessagingResponse()
    resp.message(balasan)
    return str(resp)


@app.route("/kirim", methods=["POST"])
def kirim_pesan():
    """Endpoint untuk mengirim pesan keluar (opsional)."""
    data = request.get_json()
    nomor_tujuan = data.get("to")
    pesan = data.get("body")

    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{nomor_tujuan}",
        body=pesan,
    )
    return {"sid": message.sid, "status": "terkirim"}, 200


@app.route("/", methods=["GET"])
def index():
    return {
        "status": "AI Agent UMKM aktif",
        "webhook": "/whatsapp",
        "produk": list(agent.data.produk.keys()),
    }


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    print("=" * 55)
    print("  AI AGENT UMKM — WHATSAPP BOT")
    print("=" * 55)
    print(f"  Twilio Number: {TWILIO_WHATSAPP_NUMBER}")
    print(f"  Webhook URL: http://localhost:5000/whatsapp")
    print("=" * 55)
    app.run(debug=True, port=5000)
