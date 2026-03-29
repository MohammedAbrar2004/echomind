"""
Manual connector for EchoMind.
Fetches mock manually uploaded documents.
"""

from datetime import datetime
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class ManualConnector(BaseConnector):
    """Manual data connector for user-uploaded documents."""
    
    def fetch_data(self) -> list[NormalizedInput]:
        """Fetch mock manually uploaded documents."""
        return [
            NormalizedInput(
                source_type="manual",
                external_message_id="manual_001",
                timestamp=datetime.now(),
                participants=["User"],
                content_type="document",
                raw_content="EchoMind project specification: A voice-driven cognitive memory system...",
                metadata={
                    "origin": "manual_upload",
                    "file_name": "echomind_spec.pdf",
                    "file_size_kb": 256
                }
            )
        ]
