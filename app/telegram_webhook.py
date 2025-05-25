import os
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def process_telegram_update(update_data: Dict[str, Any]) -> None:
    """Process incoming Telegram update"""
    try:
        logger.info(f"Processing update: {json.dumps(update_data, indent=2)}")
        
        # Handle message updates
        if 'message' in update_data:
            handle_message(update_data['message'])
        
        # Handle callback query (inline keyboard buttons)
        elif 'callback_query' in update_data:
            handle_callback_query(update_data['callback_query'])
            
        else:
            logger.warning(f"Unhandled update type: {list(update_data.keys())}")
            
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)

def handle_message(message: Dict[str, Any]) -> None:
    """Handle incoming message"""
    try:
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        logger.info(f"Received message from chat {chat_id}: {text}")
        
        # Handle commands
        if text.startswith('/'):
            handle_command(chat_id, text)
        else:
            # Handle regular text message
            handle_text_message(chat_id, text)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        send_error_message(message['chat']['id'], "Maaf, terjadi kesalahan saat memproses pesan Anda.")

def handle_command(chat_id: int, command: str) -> None:
    """Handle bot commands"""
    try:
        if command == '/start':
            welcome_text = """🏗️ **Selamat datang di Bot AI Konstruksi & Pajak!**

Saya adalah asisten AI yang dapat membantu Anda dalam:

🔹 **Analisis Dokumen Konstruksi**
   • PDF, Word, Excel
   • Gambar teknis (OCR)
   
🔹 **Perhitungan Konstruksi**
   • Volume material
   • Estimasi biaya
   • Analisis pajak

🔹 **Knowledge Base**
   • Simpan dokumen penting
   • Referensi cepat

**Cara menggunakan:**
• Kirim dokumen untuk dianalisis
• Ketik pertanyaan tentang konstruksi
• Gunakan /help untuk bantuan lengkap

Mari mulai! Apa yang dapat saya bantu hari ini? 🚀"""
            
            send_message(chat_id, welcome_text)
            
        elif command == '/help':
            help_text = """📋 **Panduan Penggunaan Bot**

**Perintah Utama:**
• `/start` - Mulai menggunakan bot
• `/help` - Tampilkan bantuan ini
• `/status` - Status sesi Anda

**Fitur Utama:**

1️⃣ **Kirim Dokumen**
   • PDF, DOCX, XLSX
   • Gambar teknis (.jpg, .png)
   
2️⃣ **Tanya AI**
   • "Hitung volume beton untuk..."
   • "Berapa biaya estimasi..."
   • "Jelaskan tentang..."

3️⃣ **Kalkulator**
   • Volume material
   • Estimasi biaya
   • Perhitungan pajak

**Tips:**
✅ Kirim dokumen dengan nama yang jelas
✅ Tanyakan hal spesifik untuk hasil terbaik
✅ Gunakan bahasa Indonesia

Butuh bantuan lebih lanjut? Silakan tanya! 😊"""
            
            send_message(chat_id, help_text)
            
        else:
            send_message(chat_id, "Perintah tidak dikenali. Ketik /help untuk melihat perintah yang tersedia.")
            
    except Exception as e:
        logger.error(f"Error handling command: {e}", exc_info=True)
        send_error_message(chat_id, "Maaf, terjadi kesalahan saat memproses perintah.")

def handle_text_message(chat_id: int, text: str) -> None:
    """Handle regular text messages"""
    try:
        # For now, send a simple AI response
        # TODO: Integrate with AI model client for intelligent responses
        
        if any(keyword in text.lower() for keyword in ['halo', 'hai', 'hello', 'hi']):
            response = """👋 Halo! Saya Bot AI Konstruksi & Pajak.

Saya siap membantu Anda dengan:
• Analisis dokumen konstruksi
• Perhitungan volume & biaya
• Konsultasi teknis konstruksi
• Analisis perpajakan

Apa yang bisa saya bantu hari ini? 🏗️"""

        elif any(keyword in text.lower() for keyword in ['terima kasih', 'thanks', 'thank you']):
            response = "Sama-sama! Senang bisa membantu. Ada lagi yang bisa saya bantu? 😊"
            
        else:
            response = f"""🤖 **Pesan diterima:** "{text}"

Saya sedang memproses permintaan Anda...

**Untuk hasil terbaik:**
• Kirim dokumen konstruksi untuk dianalisis
• Tanyakan hal spesifik tentang konstruksi
• Gunakan /help untuk panduan lengkap

Fitur AI penuh sedang dalam pengembangan! 🚀"""

        send_message(chat_id, response)
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        send_error_message(chat_id, "Maaf, terjadi kesalahan saat memproses pesan Anda.")

def handle_callback_query(callback_query: Dict[str, Any]) -> None:
    """Handle callback queries from inline keyboards"""
    try:
        # TODO: Implement callback query handling
        logger.info(f"Received callback query: {callback_query}")
        
    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)

def send_message(chat_id: int, text: str, parse_mode: str = 'Markdown') -> Optional[Dict]:
    """Send message to Telegram chat"""
    try:
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment")
            return None
            
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Message sent successfully to chat {chat_id}")
            return response.json()
        else:
            logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {e}", exc_info=True)
        return None

def send_error_message(chat_id: int, error_text: str) -> None:
    """Send formatted error message"""
    try:
        formatted_error = f"❌ **Error**\n\n{error_text}\n\nSilakan coba lagi atau hubungi admin jika masalah berlanjut."
        send_message(chat_id, formatted_error)
        
    except Exception as e:
        logger.error(f"Error sending error message: {e}", exc_info=True)