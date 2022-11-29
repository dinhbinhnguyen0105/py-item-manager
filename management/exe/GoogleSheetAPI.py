import os.path
from pathlib import Path
from re import T
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from httplib2.error import ServerNotFoundError

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_NAME = 'ItemsForShell'
WORKSHEET_NAME = 'ItemsDetail'
WORKSHEET_HEADER = [
    'Date',
    'Category', 
    'Ward', 
    'Road', 
    'Area', 
    'Pirce', 
    'Width',
    'Construction',
    'Function',
    'Furiture',
    'Building line',
    'Legal',
    'Description',
    'Notes',
    'Folder',
    'Images ID',
    'Images name'
]

class GoogleSheet():
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
        self.service_spreadsheet = build('sheets', 'v4', credentials = creds)
        self._notification('sheets_v4', 'service created successfully', 'mess')

        self.spread_id = None
        self.worksheet_name = WORKSHEET_NAME
        try:
            for i in range(10):
                try:
                    self.spread_id = self._isExist(SPREADSHEET_NAME)
                    if not self.spread_id:
                        self.spread_id = self._create(SPREADSHEET_NAME, WORKSHEET_NAME)
                        self._notification(SPREADSHEET_NAME, message = 'created successfully')
                        self._update(self.spread_id, WORKSHEET_NAME, WORKSHEET_HEADER)
                        self._notification(WORKSHEET_NAME, message = 'successfully renamed')
                        break
                    else:
                        break
                except TimeoutError as error:
                    self._notification(error, notification='error')
                    self._notification('Reconnecting ...', message=f'[{i + 1}]', notification='mess')
        except ServerNotFoundError as e_servernotfound:
            self._notification(e_servernotfound, notification='error')

    def _create(self, sheet_name, worksheet_name):
        spreadsheet = {
            'properties' : {
                'title' : sheet_name
            }
        }
        spreadsheet = self.service_spreadsheet.spreadsheets().create(
            body = spreadsheet,
            fields = 'spreadsheetId'
        ).execute()

        self._renameWorksheet(spreadsheet.get('spreadsheetId'), worksheet_name)

        return spreadsheet.get('spreadsheetId')

    def _get(self, spread_id):
        
        try:
            for i in range(10):
                try:
                    response = self.service_spreadsheet.spreadsheets().values().get(
                        spreadsheetId = spread_id,
                        range = WORKSHEET_NAME
                    ).execute()
                    self._notification('Data', 'is available')
                    return response.get('values')
                except TimeoutError as error:
                    self._notification(error, notification='error')
                    self._notification('Reconnecting ...', message=f'[{i + 1}]', notification='mess')
        except ServerNotFoundError as e_servernotfound:
            self._notification(e_servernotfound, notification='error')
        

    def _update(self, spread_id, worksheet_name, header):
        response = self.service_spreadsheet.spreadsheets().values().update(
            spreadsheetId = spread_id,
            range = f'{worksheet_name}!A1',
            valueInputOption = 'USER_ENTERED',
            body = {
                'values' : [header]
            }
        ).execute()

        return response

    def _append(self, spread_id, data):
        values = self._get(spread_id)
        response = None
        if len(values[0]) != len(data):
            self._notification('Mismatched', 'input does not match the title ', 'error')
            print(values)
            print(data)
            return False
        else:
            response = self.service_spreadsheet.spreadsheets().values().append(
                spreadsheetId = spread_id,
                range = f'{WORKSHEET_NAME}!A{len(values) + 1}',
                valueInputOption = 'USER_ENTERED',
                insertDataOption = 'INSERT_ROWS',
                body = {
                    'values' : [data]
                }
            ).execute()
            self._notification('Appended', 'data')
            return response.get('updates')
            
    def _clear(self, spread_id, worsheet_name, row):
        for i in range(10):
            try:
                response = self.service_spreadsheet.spreadsheets().values().clear(
                spreadsheetId = spread_id,
                range = f'{worsheet_name}!{row}:{row}'
                ).execute()
                self._notification(f'{response.get("clearedRange")}', 'has been deleted')
                return response
            except TimeoutError as error:
                self._notification(error, notification='error')
                self._notification('Reconnecting ...', message=f'[{i + 1}]', notification='mess')
        return False

    def _isExist(self, file_name):
        page_token = None
        while True:
            respones = self.service_drive.files().list(
                q = 'mimeType = "application/vnd.google-apps.spreadsheet"',
                spaces = 'drive',
                fields = 'nextPageToken, files(id, name)',
                pageToken = page_token,
            ).execute()

            for file in respones.get('files', []):
                if file.get('name') == file_name:
                    self._notification(file_name, 'is available')
                    return file.get('id')
            page_token = respones.get(
                'nextPageToken',
                None
            )
            if page_token is None:
                self._notification(file_name, 'is unavailable')
                return False
 
    def _renameWorksheet(self, spread_id, worksheet_name):
        response = self.service_spreadsheet.spreadsheets().get(
           spreadsheetId = spread_id
        ).execute()
        mysheet = None

        for sheet in response['sheets']:
            mysheet = {
                    'sheetId' : sheet['properties']['sheetId'],
                    'title' : sheet['properties']['title']
            }
            
        request_body = {
            'requests' : [
                {
                    'updateSheetProperties' : {
                        'properties' : {
                            'sheetId' : mysheet['sheetId'],
                            'title' : worksheet_name
                        },
                        'fields' : 'title'
                    }
                }
            ]
        }
        self.service_spreadsheet.spreadsheets().batchUpdate(
            spreadsheetId = spread_id,
            body = request_body
        ).execute()
        
    def _notification(self, object, message = '', notification = 'mess'):
        if notification == 'mess':
            print(f'[MESSAGES] : <{object}> {message}.')
        if notification == 'error':
            print(f'[ERORR] : {object}.')


# if __name__ == '__main__':
#     google = GoogleSheet()
#     # google._append('1a4Q6Z8OIbFMqwjdJqM6kvzekEkng9-8iOnOSbc28mKI', WORKSHEET_NAME, ['Danh muc', 'Đường', 'Phường', 'Diện tích', 'Ngang', 'Kết cấu', 'Công năng', 'Nội thất', 'Lộ giới', 'Pháp lý', 'Mô tả', 'Giá', 'Hình ảnh', 'Nguồn'])
#     # google._clear('1a4Q6Z8OIbFMqwjdJqM6kvzekEkng9-8iOnOSbc28mKI', WORKSHEET_NAME, 2)
#     print(google._get(google.spread_id, WORKSHEET_NAME))

