"""
Gmail connector for EchoMind.
Fetches real emails via Gmail API with OAuth authentication.
Extracts body text and attachments, normalizes to NormalizedInput format.
"""

import os
import pickle
import base64
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_python_client import build
from googleapiclient.errors import HttpError

from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput
from app.services.media_service import MediaService


class GmailConnector(BaseConnector):
    """Gmail data connector with OAuth authentication."""
    
    # Gmail API scope
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    # Supported attachment MIME types
    SUPPORTED_ATTACHMENTS = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    
    def __init__(self):
        """Initialize Gmail connector with OAuth credentials."""
        super().__init__()
        self.connector_dir = Path(__file__).parent
        self.credentials_path = self.connector_dir / 'credentials.json'
        self.token_path = self.connector_dir / 'token.json'
        self.service = None
        self.media_service = MediaService()
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token_file:
                creds = pickle.load(token_file)
        
        # Refresh or request new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[GmailConnector] Token refresh failed: {e}")
                creds = None
        
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"Gmail credentials.json not found at {self.credentials_path}. "
                    "Download it from Google Cloud Console."
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save token for next run
                with open(self.token_path, 'wb') as token_file:
                    pickle.dump(creds, token_file)
            except Exception as e:
                raise RuntimeError(f"Gmail OAuth authentication failed: {e}")
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch unread emails from Gmail inbox.
        Extract body text and attachments, create NormalizedInput objects.
        Mark emails as read after successful processing.
        """
        results = []
        
        if not self.service:
            print("[GmailConnector] Not authenticated")
            return results
        
        try:
            # Fetch unread messages from inbox
            messages = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=10
            ).execute().get('messages', [])
            
            print(f"[GmailConnector] Found {len(messages)} unread emails")
            
            for message in messages:
                try:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = msg['payload']['headers']
                    email_id = msg['id']
                    thread_id = msg['threadId']
                    
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                    from_addr = next((h['value'] for h in headers if h['name'] == 'From'), '')
                    to_addr = next((h['value'] for h in headers if h['name'] == 'To'), '')
                    date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # Parse email date
                    try:
                        email_date = datetime.fromisoformat(
                            date_str.replace(' GMT', '').replace(' +0000', '')
                        )
                        if email_date.tzinfo is None:
                            email_date = email_date.replace(tzinfo=None)
                    except:
                        email_date = datetime.now()
                    
                    # Extract participants
                    participants = list(set(
                        [from_addr] + [to_addr] 
                        if to_addr else [from_addr]
                    ))
                    participants = [p.strip() for p in participants if p.strip()]
                    
                    # Extract body text
                    body_text = self._extract_body(msg['payload'])
                    
                    # Create NormalizedInput for the email body
                    if body_text.strip():
                        results.append(NormalizedInput(
                            source_type="gmail",
                            external_message_id=f"{email_id}_body",
                            timestamp=email_date,
                            participants=participants,
                            content_type="email",
                            raw_content=body_text,
                            metadata={
                                "subject": subject,
                                "email_id": email_id,
                                "thread_id": thread_id,
                                "origin": "gmail"
                            },
                            media=None
                        ))
                    
                    # Extract and process attachments
                    attachments = self._extract_attachments(msg['payload'], email_id)
                    for filename, mime_type, data in attachments:
                        try:
                            # Save attachment via MediaService
                            media_obj = self.media_service.save(
                                raw_bytes=data,
                                original_filename=filename,
                                mime_type=mime_type,
                                source_type="gmail",
                                captured_at=email_date
                            )
                            
                            # Create NormalizedInput for attachment
                            results.append(NormalizedInput(
                                source_type="gmail",
                                external_message_id=f"{email_id}_attachment_{filename}",
                                timestamp=email_date,
                                participants=participants,
                                content_type="document",
                                raw_content="",
                                metadata={
                                    "subject": subject,
                                    "email_id": email_id,
                                    "thread_id": thread_id,
                                    "filename": filename,
                                    "origin": "gmail_attachment"
                                },
                                media=[media_obj]
                            ))
                        except Exception as e:
                            print(f"[GmailConnector] Failed to process attachment {filename}: {e}")
                            continue
                    
                    # Mark email as read
                    try:
                        self.service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                    except Exception as e:
                        print(f"[GmailConnector] Failed to mark email as read: {e}")
                
                except Exception as e:
                    print(f"[GmailConnector] Error processing email {message['id']}: {e}")
                    continue
            
            print(f"[GmailConnector] Successfully processed {len(results)} items")
            return results
        
        except HttpError as e:
            print(f"[GmailConnector] Gmail API error: {e}")
            return results
        except Exception as e:
            print(f"[GmailConnector] Unexpected error: {e}")
            return results
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload, preferring plain text."""
        body = ""
        
        # Check for direct body (simple emails)
        if 'body' in payload and payload['body'].get('data'):
            try:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                return body
            except:
                pass
        
        # Check for parts (multipart emails)
        if 'parts' in payload:
            text_body = ""
            html_body = ""
            
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    try:
                        text_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                    except:
                        pass
                
                elif mime_type == 'text/html' and part.get('body', {}).get('data'):
                    try:
                        html_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                    except:
                        pass
                
                # Recursively check nested parts
                elif mime_type.startswith('multipart/'):
                    nested = self._extract_body(part)
                    if nested:
                        body = nested
            
            # Prefer plain text, fall back to HTML stripped
            if text_body:
                return text_body
            elif html_body:
                return self._strip_html(html_body)
        
        return body
    
    def _extract_attachments(self, payload: dict, email_id: str) -> list[tuple]:
        """Extract supported attachments from payload."""
        attachments = []
        
        if 'parts' not in payload:
            return attachments
        
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            
            # Skip if unsupported MIME type
            if mime_type not in self.SUPPORTED_ATTACHMENTS:
                continue
            
            # Check for attachment
            if 'filename' not in part.get('headers', []):
                continue
            
            filename = part.get('filename', 'unknown')
            if not filename:
                continue
            
            # Get attachment data
            try:
                if 'data' in part.get('body', {}):
                    data = base64.urlsafe_b64decode(part['body']['data'])
                else:
                    # Attachment stored separately, fetch via attachmentId
                    att_id = part.get('body', {}).get('attachmentId')
                    if att_id:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=email_id,
                            id=att_id
                        ).execute()
                        data = base64.urlsafe_b64decode(attachment['data'])
                    else:
                        continue
                
                attachments.append((filename, mime_type, data))
            except Exception as e:
                print(f"[GmailConnector] Failed to extract attachment {filename}: {e}")
                continue
        
        return attachments
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags and decode entities."""
        # Remove style and script tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
