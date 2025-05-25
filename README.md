Telegram AI Assistant untuk Dunia Konstruksi

Telegram AI Assistant adalah bot cerdas berbasis Python yang dirancang khusus untuk mendukung kebutuhan teknis dan administratif di dunia konstruksi. Bot ini menggunakan integrasi AI (LLM seperti Together.ai), OCR, dan regulasi watcher untuk membantu memahami dokumen, menghitung biaya, hingga memantau pembaruan regulasi.

================================================================================

Fitur Utama:
1. Chatbot AI responsif dan kontekstual (memahami chat sebelumnya)
2. Membaca & memahami dokumen: PDF, Word (DOCX), Excel (XLSX), dan gambar
3. OCR cerdas untuk denah teknis, potongan bangunan, DED, dll
4. Ekstraksi & klasifikasi data teknis atau perpajakan
5. Perhitungan otomatis: volume, biaya, dan kebutuhan material
6. Estimasi pajak konstruksi (PPh Final, dll)
7. Ringkasan cerdas dokumen panjang (AiSmart Summary)
8. Gaya jawaban khusus dan prompt preset
9. Mode kerja normal & mode khusus untuk ringkasan
10. Modul pantau regulasi (PUPR & DJP) secara real-time
11. Integrasi Telegram penuh (inline keyboard, perintah, file upload)

================================================================================

Arsitektur:
- Telegram Webhook Gateway
- Dispatcher Logika
- Prompt & Memory System
- AI Engine (LLM API)
- Analisis Dokumen: parser PDF, DOCX, XLSX, OCR
- Knowledge Base internal & eksternal (vector store)
- Regulasi Watcher
- Penyimpanan SQLite

================================================================================

Struktur Folder:
bot-ai/
├── main.py
├── config.yaml
├── requirements.txt
├── .env
│
├── app/
│   ├── telegram_webhook.py
│   ├── dispatcher.py
│   ├── response_format.py
│   ├── prompt_engine.py
│   └── memory_store.py
│
├── ai_core/
│   ├── model_client.py
│   ├── context_builder.py
│   └── summarizer.py
│
├── document_handler/
│   ├── parser_pdf.py
│   ├── parser_docx.py
│   ├── parser_xlsx.py
│   ├── image_ocr.py
│   └── classifier.py
│
├── knowledge_base/
│   ├── internal_kb.json
│   ├── external_kb_vector/
│   ├── retriever.py
│   └── loader.py
│
├── regulasi_watcher/
│   ├── scraper.py
│   ├── extractor.py
│   ├── classifier.py
│   ├── change_detector.py
│   └── updater.py
│
├── db/
│   ├── chat_logs.sqlite
│   └── documents/
│
└── utils/
    ├── logger.py
    ├── file_utils.py
    └── time_utils.py

================================================================================

Cara Menjalankan:
1. Clone repo: git clone https://github.com/username/bot-ai.git
2. Install dependencies: pip install -r requirements.txt
3. Siapkan .env dan config.yaml
4. Jalankan bot: python main.py

Lisensi: MIT License
Kontak: your@email.com