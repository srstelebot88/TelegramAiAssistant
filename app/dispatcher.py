import logging
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from models import ChatSession, ChatMessage, DocumentUpload
from app import db
from app.memory_store import MemoryStore
from app.prompt_engine import PromptEngine
from app.response_format import ResponseFormatter
from ai_core.model_client import AIModelClient
from document_handler.classifier import DocumentClassifier
from knowledge_base.retriever import KnowledgeRetriever
from utils.logger import get_logger
from utils.file_utils import save_uploaded_file
from utils.construction_calc import ConstructionCalculator

logger = get_logger(__name__)

class TelegramDispatcher:
    """Main dispatcher for handling Telegram updates"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.memory_store = MemoryStore()
        self.prompt_engine = PromptEngine()
        self.response_formatter = ResponseFormatter()
        self.ai_client = AIModelClient()
        self.doc_classifier = DocumentClassifier()
        self.knowledge_retriever = KnowledgeRetriever()
        self.construction_calc = ConstructionCalculator()
        
    def process_update(self, update: Update) -> None:
        """Process incoming Telegram update"""
        try:
            if update.message:
                self._handle_message(update)
            elif update.callback_query:
                self._handle_callback_query(update)
            else:
                logger.debug(f"Unhandled update type: {type(update)}")
                
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}", exc_info=True)
            if update.message:
                self._send_error_message(update.message.chat_id, "Terjadi kesalahan dalam memproses pesan Anda.")
    
    def _handle_message(self, update: Update) -> None:
        """Handle incoming message"""
        message = update.message
        user = message.from_user
        chat_id = message.chat_id
        
        # Get or create chat session
        session = self._get_or_create_session(user)
        
        # Store user message
        self._store_message(session.id, 'user', message.text or '[File/Media]', str(message.message_id))
        
        try:
            if message.text:
                if message.text.startswith('/'):
                    self._handle_command(message, session)
                else:
                    self._handle_text_message(message, session)
            elif message.document or message.photo:
                self._handle_file_upload(message, session)
            else:
                self._send_message(chat_id, "Maaf, saya hanya dapat memproses teks dan dokumen.")
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            self._send_error_message(chat_id, "Terjadi kesalahan dalam memproses pesan Anda.")
    
    def _handle_command(self, message, session: ChatSession) -> None:
        """Handle bot commands"""
        command = message.text.split()[0].lower()
        chat_id = message.chat_id
        
        if command == '/start':
            welcome_text = """🏗️ Selamat datang di AI Construction & Tax Bot! 🏗️

Saya adalah asisten AI yang dapat membantu Anda dengan:
• 📋 Analisis dokumen konstruksi (PDF, DOCX, XLSX)
• 📐 Perhitungan volume dan estimasi biaya
• 🧮 Estimasi pajak konstruksi
• 📊 OCR untuk gambar teknis dan denah
• 💬 Konsultasi konstruksi dan pajak

Pilih menu di bawah untuk memulai:"""
            
            keyboard = [
                [InlineKeyboardButton("📄 Upload Dokumen", callback_data="upload_doc")],
                [InlineKeyboardButton("🧮 Kalkulator Konstruksi", callback_data="calculator")],
                [InlineKeyboardButton("💬 Chat AI", callback_data="chat_ai")],
                [InlineKeyboardButton("📚 Knowledge Base", callback_data="knowledge")],
                [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            self._send_message(chat_id, welcome_text, reply_markup=reply_markup)
            
        elif command == '/help':
            self._send_help_message(chat_id)
            
        elif command == '/clear':
            self.memory_store.clear_memory(session.id)
            self._send_message(chat_id, "✅ Riwayat percakapan telah dihapus.")
            
        elif command == '/status':
            self._send_status_message(chat_id, session)
            
        else:
            self._send_message(chat_id, "Perintah tidak dikenali. Ketik /help untuk melihat daftar perintah.")
    
    def _handle_text_message(self, message, session: ChatSession) -> None:
        """Handle regular text messages"""
        user_text = message.text
        chat_id = message.chat_id
        
        # Show typing indicator
        self.bot.send_chat_action(chat_id, 'typing')
        
        # Build context from memory
        context = self.memory_store.get_context(session.id)
        
        # Build prompt
        prompt = self.prompt_engine.build_conversation_prompt(user_text, context)
        
        # Get AI response
        ai_response = self.ai_client.generate_response(prompt)
        
        if ai_response:
            # Format response
            formatted_response = self.response_formatter.format_message(ai_response)
            
            # Send response
            self._send_message(chat_id, formatted_response, parse_mode=ParseMode.MARKDOWN)
            
            # Store messages
            self._store_message(session.id, 'bot', ai_response)
            
            # Update memory
            self.memory_store.update_memory(session.id, user_text, ai_response)
        else:
            self._send_error_message(chat_id, "Maaf, saya tidak dapat memproses permintaan Anda saat ini.")
    
    def _handle_file_upload(self, message, session: ChatSession) -> None:
        """Handle file uploads"""
        chat_id = message.chat_id
        
        try:
            # Show processing indicator
            self.bot.send_chat_action(chat_id, 'upload_document')
            
            if message.document:
                file_info = self.bot.get_file(message.document.file_id)
                filename = message.document.file_name
                file_size = message.document.file_size
            elif message.photo:
                # Get the largest photo
                photo = max(message.photo, key=lambda x: x.file_size)
                file_info = self.bot.get_file(photo.file_id)
                filename = f"image_{photo.file_id}.jpg"
                file_size = photo.file_size
            else:
                self._send_message(chat_id, "Tipe file tidak didukung.")
                return
            
            # Save file
            file_path = save_uploaded_file(file_info, filename)
            
            # Store in database
            doc_upload = DocumentUpload(
                session_id=session.id,
                filename=filename,
                file_path=file_path,
                file_type=filename.split('.')[-1].lower() if '.' in filename else 'unknown',
                file_size=file_size
            )
            db.session.add(doc_upload)
            db.session.commit()
            
            # Process document
            self._process_document(chat_id, doc_upload)
            
        except Exception as e:
            logger.error(f"Error handling file upload: {str(e)}", exc_info=True)
            self._send_error_message(chat_id, "Gagal memproses file yang diunggah.")
    
    def _process_document(self, chat_id: int, doc_upload: DocumentUpload) -> None:
        """Process uploaded document"""
        try:
            # Classify and extract content
            result = self.doc_classifier.process_document(doc_upload.file_path, doc_upload.file_type)
            
            if result:
                # Update processing result
                doc_upload.processed = True
                doc_upload.processing_result = result.get('extracted_text', '')
                db.session.commit()
                
                # Format and send response
                response = self.response_formatter.format_document_analysis(result)
                self._send_message(chat_id, response, parse_mode=ParseMode.MARKDOWN)
                
                # Offer additional analysis
                keyboard = [
                    [InlineKeyboardButton("📊 Analisis Lebih Detail", callback_data=f"analyze_{doc_upload.id}")],
                    [InlineKeyboardButton("🧮 Hitung Estimasi", callback_data=f"estimate_{doc_upload.id}")],
                    [InlineKeyboardButton("💾 Simpan ke Knowledge Base", callback_data=f"save_kb_{doc_upload.id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                self._send_message(chat_id, "Apa yang ingin Anda lakukan selanjutnya?", reply_markup=reply_markup)
            else:
                self._send_error_message(chat_id, "Gagal memproses dokumen. Pastikan format file didukung.")
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            self._send_error_message(chat_id, "Terjadi kesalahan saat memproses dokumen.")
    
    def _handle_callback_query(self, update: Update) -> None:
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        query.answer()
        
        chat_id = query.message.chat_id
        data = query.data
        
        try:
            if data == "upload_doc":
                self._send_upload_instructions(chat_id)
            elif data == "calculator":
                self._send_calculator_menu(chat_id)
            elif data == "chat_ai":
                self._send_message(chat_id, "💬 Mode Chat AI aktif. Silakan kirim pertanyaan Anda tentang konstruksi atau pajak.")
            elif data == "knowledge":
                self._send_knowledge_menu(chat_id)
            elif data == "help":
                self._send_help_message(chat_id)
            elif data.startswith("analyze_"):
                doc_id = int(data.split("_")[1])
                self._analyze_document_detail(chat_id, doc_id)
            elif data.startswith("estimate_"):
                doc_id = int(data.split("_")[1])
                self._calculate_estimate(chat_id, doc_id)
            elif data.startswith("save_kb_"):
                doc_id = int(data.split("_")[1])
                self._save_to_knowledge_base(chat_id, doc_id)
            else:
                self._send_message(chat_id, "Aksi tidak dikenali.")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {str(e)}", exc_info=True)
            self._send_error_message(chat_id, "Terjadi kesalahan dalam memproses aksi.")
    
    def _get_or_create_session(self, user) -> ChatSession:
        """Get existing session or create new one"""
        session = ChatSession.query.filter_by(telegram_user_id=str(user.id)).first()
        
        if not session:
            session = ChatSession(
                telegram_user_id=str(user.id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.session.add(session)
            db.session.commit()
        
        return session
    
    def _store_message(self, session_id: int, message_type: str, content: str, telegram_msg_id: str = None) -> None:
        """Store message in database"""
        message = ChatMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            telegram_message_id=telegram_msg_id
        )
        db.session.add(message)
        db.session.commit()
    
    def _send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode=None) -> None:
        """Send message to Telegram chat"""
        try:
            self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except TelegramError as e:
            logger.error(f"Failed to send message: {str(e)}")
    
    def _send_error_message(self, chat_id: int, error_text: str) -> None:
        """Send formatted error message"""
        self._send_message(chat_id, f"❌ {error_text}")
    
    def _send_help_message(self, chat_id: int) -> None:
        """Send help message"""
        help_text = """🆘 **Panduan Penggunaan Bot**

**Perintah Utama:**
• `/start` - Mulai menggunakan bot
• `/help` - Tampilkan bantuan
• `/clear` - Hapus riwayat percakapan
• `/status` - Status session Anda

**Fitur Utama:**
• **Upload Dokumen**: Kirim file PDF, DOCX, XLSX untuk dianalisis
• **Chat AI**: Tanya jawab tentang konstruksi dan pajak
• **Kalkulator**: Perhitungan volume dan estimasi biaya
• **OCR**: Analisis gambar teknis dan denah

**Format File Didukung:**
• PDF, DOCX, XLSX (maks 50MB)
• PNG, JPG, JPEG untuk OCR

**Tips:**
• Berikan konteks yang jelas dalam pertanyaan
• Upload dokumen satu per satu untuk hasil optimal
• Gunakan /clear jika ingin memulai percakapan baru"""

        self._send_message(chat_id, help_text, parse_mode=ParseMode.MARKDOWN)
    
    def _send_upload_instructions(self, chat_id: int) -> None:
        """Send file upload instructions"""
        text = """📄 **Panduan Upload Dokumen**

Silakan kirim file dengan format:
• 📋 PDF - Dokumen RAB, spesifikasi teknis
• 📝 DOCX - Kontrak, laporan
• 📊 XLSX - Data biaya, volume
• 🖼️ Gambar - Denah, potongan (PNG, JPG)

**Maksimal ukuran file: 50MB**

Setelah upload, saya akan:
• 🔍 Menganalisis isi dokumen
• 📊 Mengekstrak data teknis
• 💰 Menghitung estimasi (jika ada data biaya)
• 📋 Memberikan ringkasan"""

        self._send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN)
    
    def _send_calculator_menu(self, chat_id: int) -> None:
        """Send calculator menu"""
        keyboard = [
            [InlineKeyboardButton("🏗️ Volume Bangunan", callback_data="calc_volume")],
            [InlineKeyboardButton("💰 Estimasi Biaya", callback_data="calc_cost")],
            [InlineKeyboardButton("🧮 Pajak Konstruksi", callback_data="calc_tax")],
            [InlineKeyboardButton("📐 Material", callback_data="calc_material")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self._send_message(
            chat_id, 
            "🧮 **Kalkulator Konstruksi**\n\nPilih jenis perhitungan:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def _send_knowledge_menu(self, chat_id: int) -> None:
        """Send knowledge base menu"""
        text = """📚 **Knowledge Base**

Akses informasi tentang:
• 📋 Standar konstruksi Indonesia (SNI)
• 💰 Panduan estimasi biaya
• 🧮 Perhitungan pajak konstruksi
• 📐 Spesifikasi material
• 📊 Analisis harga satuan

Ketik pertanyaan Anda atau pilih topik di bawah:"""

        keyboard = [
            [InlineKeyboardButton("📋 SNI & Standar", callback_data="kb_standards")],
            [InlineKeyboardButton("💰 Estimasi Biaya", callback_data="kb_costing")],
            [InlineKeyboardButton("🧮 Pajak Konstruksi", callback_data="kb_tax")],
            [InlineKeyboardButton("📐 Material & Spek", callback_data="kb_materials")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self._send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _send_status_message(self, chat_id: int, session: ChatSession) -> None:
        """Send session status"""
        message_count = ChatMessage.query.filter_by(session_id=session.id).count()
        doc_count = DocumentUpload.query.filter_by(session_id=session.id).count()
        
        status_text = f"""📊 **Status Session Anda**

👤 **User**: {session.first_name or 'Unknown'}
🆔 **Session ID**: {session.id}
📅 **Dibuat**: {session.created_at.strftime('%d/%m/%Y %H:%M')}
💬 **Total Pesan**: {message_count}
📄 **Dokumen Upload**: {doc_count}
🕒 **Aktivitas Terakhir**: {session.last_activity.strftime('%d/%m/%Y %H:%M')}"""

        self._send_message(chat_id, status_text, parse_mode=ParseMode.MARKDOWN)
    
    def _analyze_document_detail(self, chat_id: int, doc_id: int) -> None:
        """Perform detailed document analysis"""
        # Implementation for detailed analysis
        self._send_message(chat_id, "🔍 Melakukan analisis detail dokumen...")
    
    def _calculate_estimate(self, chat_id: int, doc_id: int) -> None:
        """Calculate cost estimate from document"""
        # Implementation for cost estimation
        self._send_message(chat_id, "💰 Menghitung estimasi biaya...")
    
    def _save_to_knowledge_base(self, chat_id: int, doc_id: int) -> None:
        """Save document to knowledge base"""
        # Implementation for saving to KB
        self._send_message(chat_id, "💾 Menyimpan ke knowledge base...")
