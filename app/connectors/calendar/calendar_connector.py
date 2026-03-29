"""
Google Calendar connector for EchoMind.
Fetches mock calendar events.
"""

from datetime import datetime
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class CalendarConnector(BaseConnector):
    """Google Calendar data connector."""
    
    def fetch_data(self) -> list[NormalizedInput]:
        """Fetch mock calendar events."""
        return [
            NormalizedInput(
                source_type="calendar",
                external_message_id="calendar_001",
                timestamp=datetime.now(),
                participants=["User", "Amaan", "Abdullah"],
                content_type="text",
                raw_content="Meeting: EchoMind Architecture Review - Discuss memory layers and semantic processing",
                metadata={"event_id": "evt_123", "duration_minutes": 60}
            )
        ]
