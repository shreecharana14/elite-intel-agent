"""
WhatsAppDelivery: Sends intelligence briefs via WhatsApp.
Supports Twilio API and Meta Business API.
"""
import os
from typing import Optional
from loguru import logger


class WhatsAppDelivery:
    """
    Delivers intelligence briefs via WhatsApp.
    Supports two backends: Twilio (easier) and Meta Business API (free).
    """

    def __init__(self):
        self.method = self._detect_method()
        logger.info(f"[WhatsApp] Using delivery method: {self.method}")

    def _detect_method(self) -> str:
        if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
            return "twilio"
        elif os.getenv("META_WA_ACCESS_TOKEN") and os.getenv("META_WA_PHONE_NUMBER_ID"):
            return "meta"
        return "none"

    def send_brief(self, brief_text: str) -> Optional[str]:
        """
        Send an intelligence brief via WhatsApp.
        Returns message SID/ID if successful.
        """
        # WhatsApp has a 4096 char limit
        if len(brief_text) > 4000:
            brief_text = brief_text[:3900] + "...\n\n[Full brief available on request]"

        if self.method == "twilio":
            return self._send_via_twilio(brief_text)
        elif self.method == "meta":
            return self._send_via_meta(brief_text)
        else:
            logger.warning("[WhatsApp] No delivery method configured. Set Twilio or Meta credentials.")
            return None

    def _send_via_twilio(self, message: str) -> Optional[str]:
        """Send via Twilio WhatsApp API."""
        try:
            from twilio.rest import Client
            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN")
            )
            msg = client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
                to=os.getenv("WHATSAPP_TO", "")
            )
            logger.info(f"[WhatsApp/Twilio] Sent. SID: {msg.sid}")
            return msg.sid
        except Exception as e:
            logger.error(f"[WhatsApp/Twilio] Send failed: {e}")
            return None

    def _send_via_meta(self, message: str) -> Optional[str]:
        """Send via Meta WhatsApp Business Cloud API."""
        try:
            import requests
            phone_number_id = os.getenv("META_WA_PHONE_NUMBER_ID")
            access_token = os.getenv("META_WA_ACCESS_TOKEN")
            recipient = os.getenv("META_WA_RECIPIENT", "")

            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            msg_id = data.get("messages", [{}])[0].get("id")
            logger.info(f"[WhatsApp/Meta] Sent. ID: {msg_id}")
            return msg_id
        except Exception as e:
            logger.error(f"[WhatsApp/Meta] Send failed: {e}")
            return None

    def send_alert(self, message: str) -> Optional[str]:
        """Send a high-priority immediate alert."""
        return self.send_brief(f"🚨 CRITICAL INTEL ALERT 🚨\n\n{message}")
