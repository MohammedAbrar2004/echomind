"""
Gmail connector for EchoMind.
Fetches mock Gmail emails.
"""

from datetime import datetime
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class GmailConnector(BaseConnector):
    """Gmail data connector."""
    
    def fetch_data(self) -> list[NormalizedInput]:
        """Fetch mock Gmail emails."""
        return [
            NormalizedInput(
                source_type="gmail",
                external_message_id="gmail_msg_001",
                timestamp=datetime.now(),
                participants=["user@gmail.com", "amaan@company.com"],
                content_type="email",
                raw_content="Hi Amaan, following up on the EchoMind discussion we had. Can we schedule a call this week?",
                metadata={"subject": "EchoMind Project Update", "email_id": "12345"}
            ),
            NormalizedInput(
                source_type="gmail",
                external_message_id="gmail_msg_002",
                timestamp=datetime.now(),
                participants=["user@gmail.com", "abdullah@company.com"],
                content_type="document",
                raw_content="Attached document: Architecture specification for EchoMind memory layers",
                metadata={
                    "origin": "attachment",
                    "file_name": "echomind_architecture.pdf",
                    "email_id": "12346"
                }
            )
        ]
