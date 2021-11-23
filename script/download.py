from __future__ import print_function
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def download_book():
    creds = None

    try:
        token = os.environ.get('GOOGLE_TOKEN_JSON')
        with open('token.json', 'w+') as token_file_tmp:
            token_file_tmp.write(token)
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        os.remove('token.json')
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        os.environ['NEW_GOOGLE_TOKEN_JSON'] = creds.to_json()
        print(creds.to_json())
    except:
        pass


    # if os.path.exists('token.json'):
    #     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     # else:
    #     #     flow = InstalledAppFlow.from_client_secrets_file(
    #     #         'credentials.json', SCOPES)
    #     #     creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open('token.json', 'w') as token:
    #         token.write(creds.to_json())

    # service = build('drive', 'v3', credentials=creds)

    # file_id = '1Ev2tXSiXdWxqVJ297qcOp2hLlutzv9MM9Q2VfLKiCgE'
    # response = service.files().export_media(fileId=file_id, mimeType='application/zip').execute()
    # with open('downloaded_book.zip', "wb") as wer:
    #     wer.write(response)
    
