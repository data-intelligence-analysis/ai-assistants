import os
from telegram import Bot
import requests

WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_TO = os.environ.get('WHATSAPP_TO')  # In international format, e.g., 15551234567

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Initialize bot only if token is available
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

def send_telegram_reports(pdf_paths):
    if not bot or not CHAT_ID:
        raise RuntimeError("Missing Telegram configuration. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
    for path in pdf_paths:
        bot.send_document(chat_id=CHAT_ID, document=open(path,'rb'))

def send_whatsapp_reports(pdf_paths):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_TO:
        raise RuntimeError("Missing WhatsApp configuration. Set WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_TO.")

    base_url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}'
    }

    for path in pdf_paths:
        filename = os.path.basename(path)
        # 1) Upload media to WhatsApp Cloud API
        with open(path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/pdf')
            }
            data = {
                'messaging_product': 'whatsapp'
            }
            upload_resp = requests.post(
                f"{base_url}/media",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
        upload_resp.raise_for_status()
        media_id = upload_resp.json().get('id')
        if not media_id:
            raise RuntimeError(f"Failed to upload PDF to WhatsApp: {upload_resp.text}")

        # 2) Send document message referencing the uploaded media
        send_payload = {
            'messaging_product': 'whatsapp',
            'to': WHATSAPP_TO,
            'type': 'document',
            'document': {
                'id': media_id,
                'filename': filename
            }
        }
        send_headers = {
            'Authorization': f'Bearer {WHATSAPP_TOKEN}',
            'Content-Type': 'application/json'
        }
        send_resp = requests.post(
            f"{base_url}/messages",
            headers=send_headers,
            json=send_payload,
            timeout=60
        )
        send_resp.raise_for_status()
    
    
