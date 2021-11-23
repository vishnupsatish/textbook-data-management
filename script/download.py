import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import requests
from requests.auth import HTTPBasicAuth
from base64 import b64encode
from nacl import encoding, public
import json
from constants import *
import shutil
import glob


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def download_book():
    """Download the HTML and ZIP HTML versions of the textbook using the Google Drive API"""
    creds = None

    token = os.environ.get('GOOGLE_TOKEN_JSON')
    with open('token.json', 'w+') as token_file_tmp:
        token_file_tmp.write(token)
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    os.remove('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())


    github_auth = HTTPBasicAuth(GITHUB_USER, os.environ.get('GITHUB_PAT'))

    public_key_request = json.loads(requests.get(f'https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/actions/secrets/public-key', auth=github_auth).text)
    public_key = public_key_request['key']
    public_key_id = public_key_request['key_id']

    payload = {'encrypted_value': encrypt(public_key, str(creds.to_json())), 'key_id': public_key_id}

    requests.put(f'https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/actions/secrets/GOOGLE_TOKEN_JSON', data=json.dumps(payload), auth=github_auth)


    shutil.rmtree('templates/images')
    os.remove('Textbook.html')
    os.remove('Textbook_images_hotlinked.html')

    
    service = build('drive', 'v3', credentials=creds)

    # Download the HTML of the book with images hotlinked
    html = service.files().export_media(fileId=FILE_ID, mimeType='text/html').execute().decode('utf-8')
    with open('Textbook_images_hotlinked.html', "w+") as book:
        book.write(html)
    

    zip_file = service.files().export_media(fileId=FILE_ID, mimeType='application/zip').execute()
    with open('downloaded_book.zip', "wb") as tmp_zip:
        tmp_zip.write(zip_file)

    shutil.unpack_archive('downloaded_book.zip', 'downloaded_book')

    os.remove('downloaded_book.zip')

    html_file = glob.glob('downloaded_book/*.html')[0]

    shutil.move(html_file, 'Textbook.html')
    shutil.move('downloaded_book/images', 'templates/images')
    shutil.rmtree('downloaded_book')

    

    # if os.path.exists('token.json'):
    #     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'credentials.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     with open('token.json', 'w') as token:
    #         token.write(creds.to_json())

    # service = build('drive', 'v3', credentials=creds)

    # file_id = '1Ev2tXSiXdWxqVJ297qcOp2hLlutzv9MM9Q2VfLKiCgE'
    # response = service.files().export_media(fileId=file_id, mimeType='application/zip').execute()
    # with open('downloaded_book.zip', "wb") as wer:
    #     wer.write(response)
    
