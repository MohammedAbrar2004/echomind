"""
Phone connector for EchoMind.
Fetches mock phone call transcripts.
"""

from datetime import datetime
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class PhoneConnector(BaseConnector):
    """Phone call data connector."""
    
    def fetch_data(self) -> list[NormalizedInput]:
        """Fetch mock phone call transcripts."""
        return [
            NormalizedInput(
                source_type="manual",
                external_message_id="phone_001",
                timestamp=datetime.now(),
                participants=["User", "Amaan"],
                content_type="transcript",
                raw_content="User: What's the timeline for Phase 1? Amaan: We should complete the ingestion pipeline by end of March.",
                metadata={"call_id": "call_456", "duration_seconds": 1200}
            )
        ]
