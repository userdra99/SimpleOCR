"""
Gmail Reader Module - Handles Gmail API integration for reading emails and downloading attachments
"""
import os
import base64
import email
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config


class GmailReader:
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self):
        """Authenticate and create Gmail API service"""
        creds = None
        
        # Check if token.json exists
        if os.path.exists(config.GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(
                config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES
            )
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(config.GMAIL_CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found: {config.GMAIL_CREDENTIALS_FILE}\n"
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(config.GMAIL_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def search_emails(self, query='', max_results=50):
        """Search for emails matching the query"""
        try:
            if not self.service:
                self.authenticate()
            
            # Build search query
            if not query:
                # Default: search for receipt-related keywords
                keyword_query = ' OR '.join([f'subject:{kw}' for kw in config.RECEIPT_KEYWORDS])
                query = f'({keyword_query})'
            
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            return messages
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_email_content(self, message_id):
        """Get email content including body and attachments"""
        try:
            if not self.service:
                self.authenticate()
            
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            # Extract email data
            payload = message['payload']
            headers = payload.get('headers', [])
            
            email_data = {
                'id': message_id,
                'subject': self._get_header(headers, 'Subject'),
                'from': self._get_header(headers, 'From'),
                'date': self._get_header(headers, 'Date'),
                'body': '',
                'attachments': []
            }
            
            # Extract body text
            email_data['body'] = self._extract_body(payload)
            
            # Extract attachments
            email_data['attachments'] = self._extract_attachments(payload, message_id)
            
            return email_data
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def _get_header(self, headers, name):
        """Get header value by name"""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ''
    
    def _extract_body(self, payload):
        """Extract email body text"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def _extract_attachments(self, payload, message_id):
        """Extract attachment information from email"""
        attachments = []
        
        def extract_from_parts(parts):
            for part in parts:
                if part.get('parts'):
                    extract_from_parts(part['parts'])
                elif part.get('filename') and part.get('body', {}).get('attachmentId'):
                    mime_type = part.get('mimeType', '')
                    if mime_type in config.SUPPORTED_ATTACHMENT_TYPES:
                        attachments.append({
                            'filename': part['filename'],
                            'mime_type': mime_type,
                            'attachment_id': part['body']['attachmentId'],
                            'message_id': message_id
                        })
        
        if 'parts' in payload:
            extract_from_parts(payload['parts'])
        
        return attachments
    
    def download_attachment(self, message_id, attachment_id, filename):
        """Download attachment from Gmail"""
        try:
            if not self.service:
                self.authenticate()
            
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            
            # Create temp directory if it doesn't exist
            os.makedirs(config.TEMP_DIR, exist_ok=True)
            
            file_path = os.path.join(config.TEMP_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return file_path
            
        except HttpError as error:
            print(f'An error occurred downloading attachment: {error}')
            return None

