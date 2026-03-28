"""
WhatsApp connector for EchoMind.
Processes WhatsApp export files from a folder with incremental ingestion support.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput


class WhatsAppConnector(BaseConnector):
    """WhatsApp data connector with incremental ingestion support."""
    
    WHATSAPP_FOLDER = "data/whatsapp"
    STATE_FILE = "data/whatsapp_state.json"
    
    def __init__(self):
        """Initialize the connector and load state."""
        self.last_message_hash = None
        self.load_state()
    
    def load_state(self):
        """Load the last processed message marker from state file."""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.last_message_hash = state.get("last_message_hash")
            except Exception as e:
                print(f"[WARNING] Failed to load state file: {e}")
                self.last_message_hash = None
    
    def save_state(self, message_hash, timestamp):
        """Save the last processed message marker to state file."""
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            state = {
                "last_message_hash": message_hash,
                "last_timestamp": timestamp.isoformat() if timestamp else None
            }
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save state file: {e}")
    
    def _generate_message_hash(self, timestamp, sender, message_text):
        """Generate a stable hash for a message."""
        hash_input = f"{timestamp.isoformat()}_{sender}_{message_text}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch and parse all WhatsApp export files from the folder.
        Supports incremental ingestion using stored marker.
        
        Returns:
            list[NormalizedInput]: Combined list of normalized messages from all files
        """
        all_messages = []
        
        # Check if folder exists
        if not os.path.exists(self.WHATSAPP_FOLDER):
            print(f"[WARNING] WhatsApp folder not found: {self.WHATSAPP_FOLDER}")
            return all_messages
        
        # Get all .txt files from the folder
        txt_files = sorted(Path(self.WHATSAPP_FOLDER).glob("*.txt"))
        
        found_last_marker = self.last_message_hash is None
        last_processed_hash = None
        last_processed_timestamp = None
        
        for file_path in txt_files:
            try:
                messages = self._parse_whatsapp_file(file_path)
                
                for msg in messages:
                    # Generate hash for this message
                    msg_hash = self._generate_message_hash(
                        msg.timestamp,
                        msg.participants[0] if msg.participants else "unknown",
                        msg.raw_content
                    )
                    
                    # Check if this is the marker message
                    if not found_last_marker and msg_hash == self.last_message_hash:
                        found_last_marker = True
                        # Skip the marker message itself, continue to next
                        continue
                    
                    # Process message if we've passed the marker (or no marker exists)
                    if found_last_marker:
                        all_messages.append(msg)
                        last_processed_hash = msg_hash
                        last_processed_timestamp = msg.timestamp
            
            except Exception as e:
                print(f"[WARNING] Error processing {file_path.name}: {e}")
                continue
        
        # Update state with last processed message
        if last_processed_hash:
            self.save_state(last_processed_hash, last_processed_timestamp)
        
        return all_messages
    
    def _parse_whatsapp_file(self, file_path: Path) -> list[NormalizedInput]:
        """
        Parse a single WhatsApp export file.
        
        Args:
            file_path: Path to the .txt file
            
        Returns:
            list[NormalizedInput]: List of parsed messages
        """
        messages = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Parse the line
                    parsed = self._parse_message_line(line)
                    
                    if parsed:
                        timestamp, sender, message_text = parsed
                        
                        # Skip system messages
                        if self._is_system_message(sender, message_text):
                            continue
                        
                        # Generate hash-based ID
                        message_hash = self._generate_message_hash(
                            timestamp,
                            sender,
                            message_text
                        )
                        
                        # Create NormalizedInput
                        normalized = NormalizedInput(
                            source_type="whatsapp",
                            external_message_id=message_hash,
                            timestamp=timestamp,
                            participants=[sender.lower()],
                            content_type="text",
                            raw_content=message_text,
                            metadata={
                                "origin": "whatsapp_export",
                                "file_name": file_path.name
                            }
                        )
                        
                        messages.append(normalized)
        
        except Exception as e:
            raise Exception(f"Failed to parse {file_path.name}: {e}")
        
        return messages
    
    def _parse_message_line(self, line: str) -> tuple or None: # type: ignore
        """
        Parse a single message line in WhatsApp format.
        
        Supports multiple formats:
        Format 1: DD/MM/YYYY, HH:MM - Sender: message
        Format 2: [M/D/YY, HH:MM:SS AM/PM] - Sender: message
        
        Args:
            line: Raw line from the WhatsApp export
            
        Returns:
            tuple: (datetime, sender, message) or None if malformed
        """
        try:
            # Remove brackets if present
            line_clean = line.strip("[]")
            
            # Find the separator " - "
            if " - " not in line_clean:
                return None
            
            # Split into timestamp part and rest
            timestamp_part, rest = line_clean.split(" - ", 1)
            timestamp_part = timestamp_part.strip()
            
            # Find the colon separator between sender and message
            if ":" not in rest:
                return None
            
            sender, message_text = rest.split(":", 1)
            sender = sender.strip()
            message_text = message_text.strip()
            
            # Parse timestamp - try multiple formats
            timestamp = None
            
            # Format 1: DD/MM/YYYY, HH:MM
            try:
                timestamp = datetime.strptime(timestamp_part, "%d/%m/%Y, %H:%M")
            except ValueError:
                pass
            
            # Format 2: M/D/YY, HH:MM:SS AM/PM
            if not timestamp:
                try:
                    timestamp = datetime.strptime(timestamp_part, "%m/%d/%y, %I:%M:%S %p")
                except ValueError:
                    pass
            
            # Format 3: M/D/YY, HH:MM
            if not timestamp:
                try:
                    timestamp = datetime.strptime(timestamp_part, "%m/%d/%y, %H:%M")
                except ValueError:
                    pass
            
            if not timestamp:
                return None
            
            return (timestamp, sender, message_text)
        
        except Exception:
            return None
    
    def _is_system_message(self, sender: str, message: str) -> bool:
        """
        Check if a message is a system message (not user-generated).
        
        Args:
            sender: Sender name
            message: Message content
            
        Returns:
            bool: True if system message, False otherwise
        """
        system_indicators = [
            "Messages and calls are encrypted",
            "Messages and calls are end-to-end encrypted",
            "left",
            "joined",
            "created group",
            "added",
            "changed the subject",
            "removed",
            "changed this group's icon",
            "updated the message timer",
            "turned off disappearing messages",
            "This message was deleted",
            "Media omitted"
        ]
        
        message_lower = message.lower()
        
        for indicator in system_indicators:
            if indicator.lower() in message_lower:
                return True
        
        return False
