"""
=============================================================
 SIMULASI AI AGENT UNTUK UMKM
 Studi Kasus 6: AI untuk UMKM - Pemasaran & Analisis Penjualan
=============================================================
 Arsitektur:
   INPUT   -> Chat WA, Transaksi, Riwayat
   PROSES  -> NLP Engine, Recommendation Engine, Forecasting
   OUTPUT  -> Auto-reply, Dashboard, Notifikasi
   BELAJAR -> Feedback Loop
=============================================================
"""

import re
from datetime import datetime
from collections import Counter, defaultdict


# ==================== WARNA TERMINAL ====================
class C:
    HEAD = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# ==================== LAPISAN 1: DATA STORE ====================
class DataStore:
    """Menyimpan semua data: produk, transaksi, feedback."""

    def __init__(self):
        self.produk = {
            "kopi susu":  {"harga": 18000, "stok": 45},
            "kopi hitam": {"harga": 12000, "stok": 30},
            "es teh":     {"harga": 8000,  "stok": 50},
            "roti bakar": {"harga": 15000, "stok": 20},
            "nasi goreng":{"harga": 20000, "stok": 15},
        }
        # (hari_ke, produk, jumlah_terjual)
        self.transaksi = [
            (1, "kopi susu", 40), (1, "es teh", 25), (1, "roti bakar", 10),
            (2, "kopi susu", 42), (2, "es teh", 30), (2, "roti bakar", 12),
            (3, "kopi susu", 38), (3, "es teh", 28), (3, "roti bakar", 8),
            (4, "kopi susu", 45), (4, "es teh", 32), (4, "roti bakar", 15),
            (5, "kopi susu", 50), (5, "es teh", 35), (5, "roti bakar", 18),
            (6, "kopi susu", 65), (6, "es teh", 40), (6, "roti bakar", 25),
            (7, "kopi susu", 30), (7, "es teh", 20), (7, "roti bakar", 7),
        ]
        self.feedback_log = []

    def cari_produk(self, teks):
        """Cari nama produk yang disebut dalam teks."""
        teks_lower = teks.lower()
        for nama in self.produk:
            if nama in teks_lower:
                return nama
        return None

    def total_terjual(self, produk):
        return sum(j for _, p, j in self.transaksi if p == produk)

    def tren_penjualan(self, produk):
        """Return list penjualan harian untuk 1 produk."""
        per_hari = defaultdict(int)
        for hari, p, j in self.transaksi:
            if p == produk:
                per_hari[hari] += j
        return [per_hari[h] for h in sorted(per_hari)]


# ==================== LAPISAN 2A: NLP ENGINE ====================
class NLPEngine:
    """Mendeteksi intent dari chat pelanggan."""

    INTENTS = {
        "sapaan":      [r"\b(halo|hai|hi|assalam|pagi|siang|sore|malam)\b"],
        "tanya_stok":  [r"(masih ada|stok|tersedia|ready|sisa)"],
        "tanya_harga": [r"(harga|berapa|brp)"],
        "pesan":       [r"(pesan|beli|order|mau|minta|ambil)"],
        "rekomendasi": [r"(rekomendasi|saran|enaknya|recommend|bagus)"],
        "prediksi":    [r"(prediksi|besok|ramalan|forecast|perkiraan)"],
        "terima_kasih":[r"(makasih|terima kasih|thanks|thx)"],
    }

    def deteksi(self, teks):
        teks_lower = teks.lower()
        for intent, patterns in self.INTENTS.items():
            for pola in patterns:
                if re.search(pola, teks_lower):
                    return intent
        return "tidak_dikenali"

    def ekstrak_jumlah(self, teks):
        """Ekstrak angka dari chat, misal 'pesan 2 kopi susu' -> 2."""
        match = re.search(r"\b(\d+)\b", teks)
        return int(match.group(1)) if match else 1


# ==================== LAPISAN 2B: RECOMMENDATION ENGINE ====================
class RecommendationEngine:
    """Kasih saran ke UMKM berdasarkan pola data."""

    def __init__(self, data: DataStore):
        self.data = data

    def produk_terlaris(self):
        counter = Counter()
        for _, p, j in self.data.transaksi:
            counter[p] += j
        return counter.most_common(3)

    def analisis_tren(self, produk):
        """Hitung persentase tren naik/turun dari data terakhir."""
        harian = self.data.tren_penjualan(produk)
        if len(harian) < 2:
            return 0
        awal = harian[0]
        akhir = harian[-1]
        return round(((akhir - awal) / awal) * 100, 1)

    def saran_harian(self):
        """Generate saran untuk UMKM hari ini."""
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
        """Kasih rekomendasi menu ke pelanggan."""
        terlaris = self.produk_terlaris()[0][0]
        return f"Rekomendasi kami: {terlaris} (paling laris minggu ini)"


# ==================== LAPISAN 2C: FORECASTING ENGINE ====================
class ForecastingEngine:
    """Prediksi penjualan besok pakai moving average + trend."""

    def __init__(self, data: DataStore):
        self.data = data

    def prediksi_besok(self, produk):
        harian = self.data.tren_penjualan(produk)
        if len(harian) < 3:
            return None
        # Simple moving average 3 hari + rata-rata growth
        ma3 = sum(harian[-3:]) / 3
        growth = (harian[-1] - harian[0]) / harian[0]
        # Bobot 70% MA + 30% trend
        prediksi = ma3 * (1 + growth * 0.3)
        return round(prediksi)

    def status_stok(self, produk):
        """Cek apakah stok cukup untuk prediksi besok."""
        prediksi = self.prediksi_besok(produk)
        stok = self.data.produk[produk]["stok"]
        if prediksi is None:
            return "Data kurang"
        if stok < prediksi:
            return f"{C.RED}KURANG!{C.END} Stok {stok} < Prediksi {prediksi}"
        return f"{C.GREEN}AMAN{C.END} (Stok {stok}, Prediksi {prediksi})"


# ==================== LAPISAN 3: AI AGENT (Orchestrator) ====================
class AIAgent:
    """Agent utama yang nyambungin semua engine."""

    def __init__(self):
        self.data = DataStore()
        self.nlp = NLPEngine()
        self.rec = RecommendationEngine(self.data)
        self.fc = ForecastingEngine(self.data)

    # ---------- HANDLE CHAT ----------
    def handle_chat(self, teks):
        intent = self.nlp.deteksi(teks)
        produk = self.data.cari_produk(teks)

        if intent == "sapaan":
            return f"Halo! Selamat datang di Warung Bu Sari 👋\nAda yang bisa kami bantu?"

        elif intent == "tanya_stok":
            if produk:
                info = self.data.produk[produk]
                return f"{produk.title()} masih ada {info['stok']} pcs ✅"
            return "Produk apa yang mau dicek stoknya, Kak?"

        elif intent == "tanya_harga":
            if produk:
                return f"Harga {produk.title()}: Rp{self.data.produk[produk]['harga']:,}"
            return f"Produk yang tersedia: {', '.join(self.data.produk.keys())}"

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

    # ---------- DASHBOARD UNTUK UMKM ----------
    def dashboard(self):
        print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════╗")
        print(f"║         DASHBOARD WARUNG BU SARI — {datetime.now().strftime('%d/%m/%Y')}        ║")
        print(f"╚══════════════════════════════════════════════════════╝{C.END}\n")

        print(f"{C.YELLOW}📊 PENJUALAN 7 HARI TERAKHIR:{C.END}")
        for nama, total in self.rec.produk_terlaris():
            tren = self.rec.analisis_tren(nama)
            simbol = "📈" if tren > 0 else "📉"
            print(f"   • {nama.title():<15} {total:>4} pcs  {simbol} {tren:+.1f}%")

        print(f"\n{C.YELLOW}🔮 PREDIKSI BESOK:{C.END}")
        for nama in self.data.produk:
            pred = self.fc.prediksi_besok(nama)
            status = self.fc.status_stok(nama)
            if pred:
                print(f"   • {nama.title():<15} ~{pred:>3} pcs  |  {status}")

        print(f"\n{C.YELLOW}💡 SARAN AI:{C.END}")
        for s in self.rec.saran_harian():
            print(f"   → {s}")

        print(f"\n{C.DIM}Total transaksi tercatat: {len(self.data.transaksi)}{C.END}\n")


# ==================== LAPISAN 4: SIMULASI CHAT ====================
def simulasi_chat():
    agent = AIAgent()

    print(f"\n{C.BOLD}{C.GREEN}╔══════════════════════════════════════════════════════╗")
    print(f"║     SIMULASI AI AGENT UMKM — WHATSAPP STYLE         ║")
    print(f"╚══════════════════════════════════════════════════════╝{C.END}")
    print(f"{C.DIM}Perintah khusus:")
    print(f"  /dashboard  → Tampilkan dashboard UMKM")
    print(f"  /prediksi   → Cek prediksi semua produk")
    print(f"  /saran      → Lihat saran AI")
    print(f"  /keluar     → Keluar{C.END}\n")

    # Simulasi chat pelanggan (demo otomatis)
    demo_chats = [
        "Halo",
        "Kopi susu masih ada?",
        "Berapa harganya?",
        "Rekomendasi minuman dong",
        "Mau pesan 2 kopi susu",
        "Terima kasih",
    ]

    print(f"{C.BOLD}=== DEMO OTOMATIS (simulasi chat pelanggan) ==={C.END}\n")
    for chat in demo_chats:
        print(f"{C.BLUE}👤 Pelanggan:{C.END} {chat}")
        print(f"{C.GREEN}🤖 AI Agent :{C.END} {agent.handle_chat(chat)}\n")

    # Interactive mode
    print(f"{C.BOLD}=== MODE INTERAKTIF ==={C.END}")
    print(f"{C.DIM}(ketik pesan lu sebagai pelanggan, atau /dashboard){C.END}\n")

    while True:
        try:
            user = input(f"{C.BLUE}👤 Pelanggan:{C.END} ").strip()
            if not user:
                continue

            if user.lower() in ("/keluar", "/exit", "exit", "quit"):
                print(f"\n{C.GREEN}Terima kasih! Simulasi selesai. 👋{C.END}\n")
                break
            elif user.lower() == "/dashboard":
                agent.dashboard()
            elif user.lower() == "/prediksi":
                print(f"\n{C.YELLOW}🔮 PREDIKSI BESOK:{C.END}")
                for nama in agent.data.produk:
                    pred = agent.fc.prediksi_besok(nama)
                    print(f"   • {nama.title():<15} ~{pred} pcs")
                print()
            elif user.lower() == "/saran":
                print(f"\n{C.YELLOW}💡 SARAN AI:{C.END}")
                for s in agent.rec.saran_harian():
                    print(f"   → {s}")
                print()
            else:
                print(f"{C.GREEN}🤖 AI Agent :{C.END} {agent.handle_chat(user)}\n")

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}Simulasi dihentikan.{C.END}\n")
            break


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    simulasi_chat()
