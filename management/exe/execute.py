from asyncore import write
import json
import os
import shutil
import unidecode

import datetime

FILE_IMAGES = 'c:\\Users\\dinhb\\Desktop\\ItemManagement\\bin\\images'

class ExecuteOnDesktop():
    def __init__(self):
        pass
    
    def createFolder(self, folder_name):
        folder_path = f'{FILE_IMAGES}\{folder_name}'
        if not os.path.isdir('{FILE_IMAGES}'):
            os.mkdir('{FILE_IMAGES}')
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        else:
            self._notification(f'{folder_name}', 'already exists')
            return folder_path
        self._notification(f'{folder_name}', 'created successfully')
        return folder_path
    def isExistFolder(self, folder_name):
        folder_path = f'{FILE_IMAGES}\{folder_name}'
        if not os.path.isdir(folder_path):
            self._notification(f'{folder_name}', 'is unavailable')
            return False
        self._notification(f'{folder_name}', 'is already exists')
        return folder_path

    def deleteFolder(self, folder_name):

        pass
    def copyFile(self, item_info, file_names):
        ls_file = []
        folder_name = self.handleFolder(item_info)
        folder_path = self.createFolder(folder_name)
        if folder_path:
            for file_name, i in zip(file_names, range(len(file_names))):
                file_extension = file_name.split('.').pop()
                file_path = f'{folder_path}\{folder_name}_{i}.{file_extension}'
                shutil.copy2(file_name, file_path)
                ls_file.append(file_path)
                self._notification(f'{file_name} to {folder_path}', 'successfully')
            return {
                'folder_name' : folder_name,
                'image_list' : ls_file
            }
        else: return False

    def writeData(self, file_name, data):
        json_object = json.dumps(data)
        with open(file_name, 'w', encoding='utf8') as file_items:
            file_items.write(json_object)
        self._notification('Data', f'saved in <{file_name}>')
    
    def readData(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf8') as file_items:
                json_object = json.load(file_items)
            return json_object
        except FileNotFoundError as filenotfounderror:
            self._notification(filenotfounderror, f'{file_name}', 'error')
            return False
    
    def handlePrice(self, price):
        _price = price.replace(',', '.')
        _price = float(_price)
        _price = int(_price*1000)
        return str(_price)

    # category_ward_road_area_price
    def handleFolder(self, item_info):
        # print(item_info[5])
        # exit()
        price = self.handlePrice(item_info[5])
        folder = f'{item_info[0]}_{item_info[1]}_P{item_info[2]}_{item_info[3]}_{price}'.replace(' ', '')
        folder = folder.lower()
        folder = unidecode.unidecode(folder)
        return folder

    def handleDate(self):
        today = datetime.date.today()
        return today.strftime('%m-%d-%y')
        pass

    def _notification(self, object, message = '', notification = 'mess'):
        if notification == 'mess':
            print(f'[MESSAGES] : <{object}> {message}.')
        if notification == 'error':
            print(f'[ERORR] : {object}.')