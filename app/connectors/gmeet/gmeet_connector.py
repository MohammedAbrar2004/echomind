"""
Google Meet connector for EchoMind.
Fetches mock Google Meet transcripts.
"""

from datetime import datetime
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class GMeetConnector(BaseConnector):
    """Google Meet data connector."""
    
    def fetch_data(self) -> list[NormalizedInput]:
        """Fetch mock Google Meet transcripts."""
        return [
            NormalizedInput(
                source_type="gmeet",
                external_message_id="gmeet_001",
                timestamp=datetime.now(),
                participants=["User", "Amaan", "Abdullah"],
                content_type="transcript",
                raw_content="Amaan: We need to finalize the memory chunking strategy. Abdullah: I suggest 400 token chunks with 50 token overlap.",
                metadata={"meeting_id": "abc123xyz", "duration_minutes": 45}
            )
        ]
