import os.path
from pathlib import Path
import mimetypes
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from httplib2.error import ServerNotFoundError

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']
FOLDER = 'ImagesForShell'


class GoogleDrive():
    def __init__(self):
        creds = None
        toke_file = Path(__file__).parent.parent.parent / 'static' / 'token.json'
        if os.path.exists(toke_file):
            creds = Credentials.from_authorized_user_file(toke_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'static\credentials.json',
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(toke_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service_drive = build('drive', 'v3', credentials=creds)
        self._notification('drive_v3', 'service created successfully', 'mess')

        try:
            for i in range(10):
                try:
                    self.id_mainFolder = self._search(FOLDER)
                    if not self.id_mainFolder:
                        self.id_mainFolder = self._create(FOLDER)
                    break
                except TimeoutError as error:
                    self._notification(error, notification='error')
                    self._notification('Reconnecting ...', message=f'[{i + 1}]', notification='mess')
                    pass
        except ServerNotFoundError as e_servernotfound:
            self._notification(e_servernotfound, notification='error')


    def _get(self):
        page_token = None
        result = None
        while True:
            response = self.service_drive.files().list(
                # q = 'mimeType = "image/jpeg"',
                spaces = 'drive',
                fields = 'nextPageToken, files(id, name, mimeType)',
                pageToken = page_token
            ).execute()
            
            result = response.get('files')

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return result
    
    def _search(self, folder_name):
        page_token = None
        while True:
            response = self.service_drive.files().list(
                q = 'mimeType : "application/vnd.google-apps.folder"',
                spaces = 'drive',
                fields = 'nextPageToken, files(id, name)',
                pageToken = page_token
            ).execute()
            for file in response.get('files', []):
                if file.get('name') == folder_name:
                    return file
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return False

    def _create(self, folder_name, folder_parent = None):
        if folder_parent == None:
            file_metadata = {
                'name' : folder_name,
                'mimeType' : 'application/vnd.google-apps.folder'
            }
        else:
            file_metadata = {
                'name' : folder_name,
                'parents' : [folder_parent],
                'mimeType' : 'application/vnd.google-apps.folder'
            }
        response = self.service_drive.files().create(
            body = file_metadata,
            fields = 'id, name'
        ).execute()
        self._notification(folder_name, 'folder created successfully')
        return response

    def _upload(self, folder_name, imgs_url):
        list_file_metadata = []
        list_media = []
        list_response = []

        folder_to_upload = self._search(folder_name)
        if not folder_to_upload:
            folder_to_upload = self._create(folder_name, self.id_mainFolder['id'])
        else:
            self._notification(folder_name, 'is exist')
            return False

        for img_url in imgs_url:
            img_name = img_url.split('\\').pop()
            list_file_metadata.append(
                {
                    'name' : f'{img_name}',
                    'parents' : [folder_to_upload['id']]
                }
            )
            list_media.append(MediaFileUpload(
                img_url,
                mimetype = mimetypes.guess_type(img_url)[0]
            ))
        for file_metadata, media in zip(list_file_metadata, list_media):
            response = self.service_drive.files().create(
                body = file_metadata,
                media_body = media,
                fields = 'parents, id, name'
            ).execute()
            self._notification(response['name'], f'successfully upload on <{folder_to_upload}>')
            list_response.append(response)
        self._notification('All', 'successfully upload')
        return list_response
        
    def _download(self, folder_name, imgs_id, imgs_name):
        for img_id, img_name in zip(imgs_id, imgs_name):
            request = self.service_drive.files().get_media(fileId=img_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fd = fh, request=request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                self._notification(img_name, 'Download progress {0}'.format(status.progress()*100))
            fh.seek(0)
            with open(os.path.join(folder_name,img_name), 'wb') as f:
                f.write(fh.read())
                f.close()
        return folder_name

    def _notification(self, object, message = '', notification = 'mess'):
        if notification == 'mess':
            print(f'[MESSAGES] : <{object}> {message}.')
        if notification == 'error':
            print(f'[ERORR] : {object}.')


if __name__ == '__main__':
    google = GoogleDrive()
    # google._create('Hello world')
    # print(google._search('Hello world'))

    mylist = [
        'c:\\Users\\dinhb\\Pictures\\Saved Pictures\\photoshopSky\\clouds_cloudy_storm_172293_2560x1440.jpg',
        'c:\\Users\\dinhb\\Pictures\\Saved Pictures\\wallpaper_2.jfif'
    ]

    print(google._upload('demoupload', mylist))
    # print(google._get())