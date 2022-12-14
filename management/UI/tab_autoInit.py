import json
from random import randint
import subprocess
from pathlib import Path


from PyQt5.QtWidgets import (
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QProgressBar,
    QTableView,
)
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    Qt,
    QSortFilterProxyModel,
    pyqtSlot,
    QRegExp,
    QAbstractTableModel
)
from management.exe.GoogleSheetAPI import GoogleSheet
from management.exe.GoogleDriveAPI import GoogleDrive
from management.exe.execute import ExecuteOnDesktop

FILE_ITEMS = 'c:\\Users\\dinhb\\Desktop\\ItemManagement\\bin\\items.json'
FILE_CONFIG = 'c:\\Users\\dinhb\\Desktop\\ItemManagement\\static\\config.json'
FOLDER_IMAGES = 'c:\\Users\\dinhb\\Desktop\\ItemManagement\\bin\\images'

class SyncDrive(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def sync(self):
        n = 0
        self.e_sheet = GoogleSheet()
        n += 1
        self.e_drive = GoogleDrive()
        n += 1
        self.e_desktop = ExecuteOnDesktop()
        n += 1
        data = self.__getDataFromSpread()
        for item in data['items'].values():
            n += 1
            self.progress.emit(n)
            item['folder'] = self.__synImages(item['info'])
        self.progress.emit(n+1)
        self.e_desktop.writeData(FILE_ITEMS, data)
        self.progress.emit(n+1)
        self.finished.emit()
        
    def __getDataFromSpread(self):
        result = self.e_sheet._get(self.e_sheet.spread_id)
        header = result.pop(0)
        data = {}
        data['header'] = header
        data['items'] = {}

        for item, index in zip(result, range(len(result))):
            data['items'][f'No_{index}'] = {}
            data['items'][f'No_{index}']['info'] = item
            # data['items'][f'No_{index}']['images']
        return data

    def __synImages(self, data):
        folder = self.e_desktop.handleFolder([data[0], data[1], data[2], data[3], data[4], data[5]])
        if not self.e_desktop.isExistFolder(folder):
            folder_save = self.e_desktop.createFolder(folder)
            if folder_save:
                ls_idimgs = data[-1].split('|')
                ls_idimgs.pop()
                ls_nameimgs = data[-2].split('|')
                ls_nameimgs.pop()
                self.e_drive._download(folder_save, ls_idimgs, ls_nameimgs)
            return folder_save
        return self.e_desktop.isExistFolder(folder)

class TableModel(QAbstractTableModel):
    def __init__(self, header, data):
        super().__init__()
        self._data = data
        self._header = header
    
    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        return len(self._data[0])
    
    def data(self, index, role = Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data[index.row()][index.column()]
                return str(value)

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            return True
        return False
    
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[section]
        return super().headerData(section, orientation, role)
    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
     
class CustomProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters = dict()

    @property
    def filters(self):
        return self._filters

    def setFilter(self, expresion, column):
        if expresion:
            self.filters[column] = expresion
        elif column in self.filters:
            del self.filters[column]
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for column, expresion in self.filters.items():
            text = self.sourceModel().index(source_row, column, source_parent).data()
            regex = QRegExp(
                expresion, Qt.CaseInsensitive, QRegExp.RegExp
            )
            if regex.indexIn(text) == -1:
                return False
        return True


class TableWidget(QWidget):
    def __init__(self, data, parent = None):
        super().__init__(parent)
        l_main = QVBoxLayout()
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)

        self.load_site(data)

        self.table.clicked.connect(self.get_item)
        
        l_main.addWidget(self.table)
        self.setLayout(l_main)
    
    def load_site(self, dataIn):
        data = []
        header = dataIn['header']
        items = dataIn['items']
        for item in items.values():
            data.append(item['info'])
        if len(data) < 1:
            return

        self.model = TableModel(header, data)
        self.proxy = CustomProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)
    
    def get_item(self):
        row_current = self.table.currentIndex().row()
        count_column = self.table.model().columnCount()
        data = []
        for count in range(count_column):
            data.append(self.table.model().index(row_current, count).data())
        return data

    @pyqtSlot(str)
    def on_date_textchanged(self, text):
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @pyqtSlot(str)
    def on_category_textchanged(self, text):
        self.proxy.setFilterKeyColumn(1)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @pyqtSlot(str)
    def on_ward_textchanged(self, text):
        self.proxy.setFilterKeyColumn(2)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @pyqtSlot(str)
    def on_street_textchanged(self, text):
        self.proxy.setFilterKeyColumn(3)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @pyqtSlot(str)
    def on_area_textchanged(self, text):
        self.proxy.setFilterKeyColumn(4)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @pyqtSlot(str)
    def on_price_textchanged(self, text):
        self.proxy.setFilterKeyColumn(5)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())


class SectionItems(QWidget):
    def __init__(self, w_content, parent = None):
        super().__init__(parent)
        self.data = None
        self._w_content = w_content
        self.initUI()

    
    def initUI(self):
        self.l_main = QVBoxLayout()
        
        self.w_progressbar = QProgressBar()        
        self.HandleThread()
        

        self.l_main.addWidget(self.w_progressbar)
        self.setLayout(self.l_main)

    def HandleThread(self):
        self.thread = QThread()

        self.sync = SyncDrive()
        self.sync.moveToThread(self.thread)

        self.thread.started.connect(self.sync.sync)
        self.thread.finished.connect(self.thread.deleteLater)

        self.sync.progress.connect(self.reportProgress)
        self.sync.finished.connect(self.sync.deleteLater)
        self.sync.finished.connect(self.thread.quit)
        self.sync.finished.connect(self.finishedProgress)

        self.thread.start()

    def reportProgress(self, n):
        self.w_progressbar.setValue(n)

    def finishedProgress(self):
        self.w_progressbar.setValue(100)
        e_desktop = ExecuteOnDesktop()
        data = e_desktop.readData(FILE_ITEMS)

        self.table = TableWidget(data) ##################################
        self.table.table.clicked.connect(lambda  : self.display_item())
        self._w_content.b_openImage.clicked.connect(lambda : self._w_content.clicked_btn_open_dialog(self.get_item()))

        self._w_content.t_output.setPlainText('Hello world')

        self.setStyleSheet('''
            QLineEdit{
                height: 30px;
                border: 1px solid #ccc;
                border-radius: 15px;
            }
        ''')
        self.filter_date = QLineEdit()
        self.filter_category = QLineEdit()
        self.filter_ward = QLineEdit()
        self.filter_street = QLineEdit()
        self.filter_area = QLineEdit()
        self.filter_price = QLineEdit()
        
        self.filter_date.setPlaceholderText('Date')
        self.filter_category.setPlaceholderText('Category')
        self.filter_ward.setPlaceholderText('Ward')
        self.filter_street.setPlaceholderText('Street')
        self.filter_area.setPlaceholderText('Area')
        self.filter_price.setPlaceholderText('Price')

        self.filter_date.textChanged.connect(self.table.on_date_textchanged)
        self.filter_category.textChanged.connect(self.table.on_category_textchanged)
        self.filter_ward.textChanged.connect(self.table.on_ward_textchanged)
        self.filter_street.textChanged.connect(self.table.on_street_textchanged)
        self.filter_area.textChanged.connect(self.table.on_area_textchanged)
        self.filter_price.textChanged.connect(self.table.on_price_textchanged)
        
        l_filter = QHBoxLayout()
        l_filter.addWidget(self.filter_date)
        l_filter.addWidget(self.filter_category)
        l_filter.addWidget(self.filter_ward)
        l_filter.addWidget(self.filter_street)
        l_filter.addWidget(self.filter_area)
        l_filter.addWidget(self.filter_price)
        self.l_main.addLayout(l_filter)
        self.l_main.addWidget(self.table)

    def get_item(self):
        data = None

        row_current = self.table.table.currentIndex().row()
        count_column = self.table.table.model().columnCount()
        data = []
        for count in range(count_column):
            data.append(self.table.table.model().index(row_current, count).data())
        return data

    def display_item(self):
        data = self.get_item()
        self._w_content.set_item(data)


class SectionContent(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.l_main = QVBoxLayout()
        self.t_output = QTextEdit()
        self.t_output.setFixedHeight(600)

        self.b_openImage = QPushButton('Open Images')
        self.l_main.addWidget(self.t_output)
        self.l_main.addWidget(self.b_openImage)
        self.setLayout(self.l_main)
    
    def set_item(self, data):
        _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description = data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12]

        with open(FILE_CONFIG, encoding='utf8') as json_file:
            data_json = json.load(json_file)
        _user_phone = data_json['user_info']['phone_number']
        _user_name = data_json['user_info']['name']
        _icons = data_json['icons']
        tags_name = data_json['tags_name']
        

        self.t_output.setPlainText(
            self.init_title(_category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons) + \
            self.init_sub_title(_category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons) + '\n' + \
            self.init_body(_category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons) + \
            '\n\n' + \
            ','.join(tags_name)
        )

    def init_title(self, _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons):
        title_1 = f'{self.rand(_icons)*2} ch??nh ch??? b??n g???p {_category}'

        if _buildingline != '???????ng xe m??y':
            title_1 += ' ' + _buildingline
        title_1 += f' {_price} t??? P. {_ward}, TP. ???? L???t\n\n'
        title_1 = title_1.upper()
        title_2 = f'b??n {_category} ph?????ng {_ward}\n\n'.upper()
        title_3 = f'b??n g???p\n\n'.upper()
        title_3 = f'b??n {_category} gi?? r???\n\n'.upper()
        title_4 = f'b??n {_category} {_street} gi?? r???\n\n'.upper()

        
        title_5 = 'H??? gi?? b??n nhanh\n\n'.upper()
        title_6 = 'Ch??nh ch??? c???n b??n\n\n'.upper()
        title_7 = 'B??n nhanh\n\n'.upper()
        title_8 = 'Ng??n h??ng si???t, b??n g???p\n\n'.upper()
        title_9 = 'Gi?? ng???p\n\n'.upper()
        title_10 = 'Gi?? trong th??ng\n\n'.upper()
        titles = [title_1, title_2, title_3, title_4, title_5, title_6, title_7, title_8, title_9, title_10]

        return self.rand(titles)

    def init_sub_title(self, _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons):
        sub_title_1 = '-------------\n'
        sub_title_ext_1 = f'Ch??? c???n b??n g???p {_category}\n'
        if _buildingline == '???????ng xe h??i':
            sub_title_ext_1 = '???????ng xe h??i r???ng r??i, thu???n ti???n di chuy???n.\n'
        elif _buildingline == 'M???t ti???n ???????ng':
            sub_title_ext_1 = 'Nh?? ngay m???t ti???n ???????ng, th??ch h???p kinh doanh bu??n b??n\n'
        else: sub_title_ext_1 = ''

        sub_title_ext_2 = ''
        if _category == '?????t':
            sub_title_ext_2 = '?????t ?????p, vu??ng v???n gi?? ?????u t??. V??? tr?? thu???n ti???n di chuy???n.\n'
        elif _category == 'Nh??':
            sub_title_ext_2 = 'Nh?? m???i, ?????p lung linh. V??? tr?? thu???n ti???n di chuy???n.\n'
        elif _category == 'Villa':
            sub_title_ext_2 = 'Villa c???c sang ch???nh. V??? tr?? thu???n ti???n di chuy???n.\n'
        elif _category == 'Kh??ch s???n':
            sub_title_ext_2 = 'Kh??ch s???n c???c x???n x??. Kinh doanh ???n ?????nh.\n'

        sub_title_ext = sub_title_ext_1 + sub_title_ext_2

        if _category == '?????t':
            sub_title_1 += 'B??n g???p l?? ?????t ph?????ng {0}, gi?? h???t d??? ch??? {1} t???. TP. ???? L???t\n'.format(_ward, _price)
            sub_title_1 += sub_title_ext_1
            sub_title_1 += 'Li??n h???: {0} - {1}\n'.format(_user_phone, _user_name)
        else:
            sub_title_1 += 'B??n g???p {0} ?????p lung linh ph?????ng {1}, gi?? ch??? {2} t???. TP. ???? L???t\n'.format(_category, _ward, _price)
            sub_title_1 += sub_title_ext_1
            sub_title_1 += 'Li??n h???: {0} - {1}\n'.format(_user_phone, _user_name)
        sub_title_1 += '-------------\n'

        sub_title_2 = f'B??n {_category} ???????ng {_street}, ph?????ng {_ward}, TP. ???? L???t\n'
        sub_title_2 += sub_title_ext

        sub_title_3 = f'B??n {_category} gi?? h???t gi??? ph?????ng {_ward}, TP. ???? L???t\n'
        sub_title_3 += sub_title_ext

        sub_title_3 = f'Ch??nh ch??? c???n b??n g???p {_category} gi?? h???t gi??? ph?????ng {_ward}, TP. ???? L???t\n'
        sub_title_3 += sub_title_ext

        sub_title_4 = f'C???c HOT, ph?????ng {_ward}, TP. ???? L???t\n'
        sub_title_4 += sub_title_ext

        sub_title_5 = f'G???P!!! {_category} ph?????ng {_ward}, TP. ???? L???t\n'
        sub_title_5 += sub_title_ext

        sub_titles = [sub_title_1, sub_title_2, sub_title_3, sub_title_4, sub_title_5]
        return self.rand(sub_titles)
    
    def init_body(self, _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _phone_number, _icons):
        body_1 = ''
        body_1 += '???? V??? tr??: ???????ng {0}, ph?????ng {1}, TP. ???? L???t\n'.format(_street, _ward)
    
        if _width != 'None':
            body_1 += '???? Di???n t??ch: {0} m2. Ngang: {1}m\n'.format(_area, _width)
        else:
            body_1 += '???? Di???n t??ch: {0} m2.\n'.format(_area)
        
        if _category != '?????t':
            body_1 += '???? K???t c???u: {0}\n'.format(_construction)
            body_1 += '???? C??ng n??ng: {0}\n'.format(_function)
            body_1 += '???? N???i th???t: {0}\n'.format(_furniture)
        body_1 += '???? L??? gi???i: {0}\n'.format(_buildingline)
        body_1 += '???? Ph??p l??: {0}\n'.format(_legal)
        body_1 += '{0} M?? t???: {1}\n'.format(self.rand(_icons) * 2, _description)
        body_1 += '{0} {1} g???n ngay trung t??m, thu???n ti???n di chuy???n, g???n c??c ti???n ??ch nh??: Ch???, tr?????ng h???c, b???nh vi???n. Khu v???c an ninh, d??n tr?? cao, th??ch h???p ?????nh c?? l??u d??i\n'.format(self.rand(_icons) * 2, _category,)
        body_1 += '???? Gi??: {0} t??? - Th????ng l?????ng\n'.format(_price)
        body_1 += '??? Li??n h???: {0} - {1}\n'.format(_phone_number, _user_name)

        body_2 = ''
        body_2 += 'V??? tr??: ???????ng {0}, ph?????ng {1}, TP. ???? L???t\n'.format(_street, _ward)
    
        if _width != 'None':
            body_2 += 'Di???n t??ch: {0} m2. Ngang: {1}m\n'.format(_area, _width)
        else:
            body_2 += 'Di???n t??ch: {0} m2.\n'.format(_area)
        
        if _category != '?????t':
            body_2 += 'K???t c???u: {0}\n'.format(_construction)
            body_2 += 'C??ng n??ng: {0}\n'.format(_function)
            body_2 += 'N???i th???t: {0}\n'.format(_furniture)
        body_2 += 'L??? gi???i: {0}\n'.format(_buildingline)
        body_2 += 'Ph??p l??: {0}\n'.format(_legal)
        body_2 += f'M?? t???: {_description}\n'
        body_2 += f'{_category} g???n ngay trung t??m, thu???n ti???n di chuy???n, g???n c??c ti???n ??ch nh??: Ch???, tr?????ng h???c, b???nh vi???n. Khu v???c an ninh, d??n tr?? cao, th??ch h???p ?????nh c?? l??u d??i\n'
        body_2 += 'Gi??: {0} t??? - Th????ng l?????ng\n'.format(_price)
        body_2 += 'Li??n h???: {0} - {1}\n'.format(_phone_number, _user_name)

        body_3 = ''
        body_3 += f'- Di???n t??ch: {_area}m2\n' 
        body_3 += f'- Ph??p l??: {_legal}\n'
        if _category != '?????t':
            body_3 += f'- K???t c???u: {_construction}. - {_function}\n'
        body_3 += f'{_buildingline}\n'
        body_3 += f'- M?? t???: {_description}\n'
        body_3 += f'- Gi??: {_price} t???\n'
        body_3 += f'- Li??n h???: 0??????9??????6??????7??????2??????6??????7??????4??????3??????8?????? - ??.B??nh'

        body_4 = ''
        body_4 += f'- Di???n t??ch: {_area}m2\n'
        body_4 += f'- Ph??p l??: {_legal}\n'
        if _category != '?????t':
            body_4 += f'- K???t c???u: {_construction}.\n'
            body_4 += f'- G???m c??: {_function}.\n'
        body_4 += f'{_buildingline}\n'
        body_4 += f'{_description}\n'
        body_4 += f'- Gi??: {_price} t???\n'
        body_4 += f'- Li??n h???: 0??????9??????6??????7??????2??????6??????7??????4??????3??????8?????? - ??.B??nh'

        body_5 = ''
        if _category != '?????t':
            body_5 += f'???????????? C???n b??n nh?? r???t xinh x???n & ???m ??p (nh?? ch??nh ch???)????????????\n'
            body_5 += f'???????? Nh?? g???m: {_construction}. {_function}\n'
            body_5 += f'???????? ??u ??i???m: {_description}\n'
            body_5 += f'???????? Ph?????ng {_ward} - TP. ???? L???t\n'
            body_5 += f'???????? Th????ng l?????ng ch??nh ch???\n'
            body_5 += f'???????? Li??n h???: {_phone_number}\n'

        body_6 = ''
        if _category != '?????t':
            body_6 += f'Gia ????nh c?? c??n nh?? c???n b??n\n'
            body_6 += f'K???t c???u: {_construction}. {_function}\n'
            body_6 += f'{_buildingline}\n'
            body_6 += f'??u ??i???m: {_description}\n'
            body_6 += f'Ph?????ng {_ward} - TP. ???? L???t\n'
            body_6 += f'- Gi??: {_price} t???\n'
            body_6 += f'Li??n h???: {_phone_number}\n'

        body_7 = ''
        if _category != '?????t':
            body_7 += f'{self.rand(_icons) * 3} B??n nh?? nh?? ?????p, xinh x???n g???n trung t??m\n'
            body_7 += f'{self.rand(_icons) * 2} Di???n t??ch: {_area}m2\n'
            body_7 += f'{self.rand(_icons) * 2} K???t c???u: {_construction}.\n'
            body_7 += f'{self.rand(_icons) * 2} C??ng n??ng: {_function}\n'
            body_7 += f'{self.rand(_icons) * 2} {_buildingline}\n'
            body_7 += f'{self.rand(_icons) * 2} ??u ??i???m: {_description}\n'
            body_7 += f'{self.rand(_icons) * 2} Ph?????ng {_ward} - TP. ???? L???t\n'
            body_7 += f'{self.rand(_icons) * 2} Gi??: {_price} t???\n'
            body_7 += f'{self.rand(_icons) * 2} Li??n h???: 0??????9??????6??????7??????2??????6??????7??????4??????3??????8??????\n'

        bodys = [body_1, body_2, body_3, body_4, body_5, body_6, body_7]


        return self.rand(bodys)

    def clicked_btn_open_dialog(self, data):
        check = False
        for i in data:
            if i is not None:
                check = True
                break
        if not check:
            return 
        e_desktop = ExecuteOnDesktop()
        folder = e_desktop.handleFolder(data)
        path = Path(__file__).parent.parent.parent.absolute()

        path = path.joinpath('bin', 'images', folder)
        
        subprocess.Popen(f'explorer /select, {path}')

    def rand(self, object):
        return object[randint(0, len(object)-1)]


class TabAutoInit(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setFixedSize(1200, 800)
        self.setStyleSheet('''
            QWidget{
                background-color: #fff;
            }
            QLineEdit{
                height: 20px;
                qproperty-frame: false;
                border-bottom: 1px solid #ccc;
            }
            QLabel{
                margin: 10px 10px;
            }
            QTextEdit{
                border: 1px solid #5f5f5f;
                border-radius: 15px;
                font-size: 15px;
            }
            QPushButton{
                height: 30px;
                border: 1px solid #000;
                border-radius: 15px;
                font-size: 15px;
            }
            QPushButton:hover{
                background-color: #ddd;

            }
        ''')

        self.mainLayout = QHBoxLayout()
        self.w_content = SectionContent()
        self.w_items = SectionItems(self.w_content)

        self.mainLayout.addWidget(self.w_items)
        self.mainLayout.addWidget(self.w_content)
        self.setLayout(self.mainLayout)

