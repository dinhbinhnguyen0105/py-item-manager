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
        title_1 = f'{self.rand(_icons)*2} chính chủ bán gấp {_category}'

        if _buildingline != 'Đường xe máy':
            title_1 += ' ' + _buildingline
        title_1 += f' {_price} tỷ P. {_ward}, TP. Đà Lạt\n\n'
        title_1 = title_1.upper()
        title_2 = f'bán {_category} phường {_ward}\n\n'.upper()
        title_3 = f'bán gấp\n\n'.upper()
        title_3 = f'bán {_category} giá rẻ\n\n'.upper()
        title_4 = f'bán {_category} {_street} giá rẻ\n\n'.upper()

        
        title_5 = 'Hạ giá bán nhanh\n\n'.upper()
        title_6 = 'Chính chủ cần bán\n\n'.upper()
        title_7 = 'Bán nhanh\n\n'.upper()
        title_8 = 'Ngân hàng siết, bán gấp\n\n'.upper()
        title_9 = 'Giá ngộp\n\n'.upper()
        title_10 = 'Giá trong tháng\n\n'.upper()
        titles = [title_1, title_2, title_3, title_4, title_5, title_6, title_7, title_8, title_9, title_10]

        return self.rand(titles)

    def init_sub_title(self, _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _user_phone, _icons):
        sub_title_1 = '-------------\n'
        sub_title_ext_1 = f'Chủ cần bán gấp {_category}\n'
        if _buildingline == 'Đường xe hơi':
            sub_title_ext_1 = 'Đường xe hơi rộng rãi, thuận tiện di chuyển.\n'
        elif _buildingline == 'Mặt tiền đường':
            sub_title_ext_1 = 'Nhà ngay mặt tiền đường, thích hợp kinh doanh buôn bán\n'
        else: sub_title_ext_1 = ''

        sub_title_ext_2 = ''
        if _category == 'Đất':
            sub_title_ext_2 = 'Đất đẹp, vuông vắn giá đầu tư. Vị trí thuận tiện di chuyển.\n'
        elif _category == 'Nhà':
            sub_title_ext_2 = 'Nhà mới, đẹp lung linh. Vị trí thuận tiện di chuyển.\n'
        elif _category == 'Villa':
            sub_title_ext_2 = 'Villa cực sang chảnh. Vị trí thuận tiện di chuyển.\n'
        elif _category == 'Khách sạn':
            sub_title_ext_2 = 'Khách sạn cực xịn xò. Kinh doanh ổn định.\n'

        sub_title_ext = sub_title_ext_1 + sub_title_ext_2

        if _category == 'Đất':
            sub_title_1 += 'Bán gấp lô đất phường {0}, giá hạt dẻ chỉ {1} tỷ. TP. Đà Lạt\n'.format(_ward, _price)
            sub_title_1 += sub_title_ext_1
            sub_title_1 += 'Liên hệ: {0} - {1}\n'.format(_user_phone, _user_name)
        else:
            sub_title_1 += 'Bán gấp {0} đẹp lung linh phường {1}, giá chỉ {2} tỷ. TP. Đà Lạt\n'.format(_category, _ward, _price)
            sub_title_1 += sub_title_ext_1
            sub_title_1 += 'Liên hệ: {0} - {1}\n'.format(_user_phone, _user_name)
        sub_title_1 += '-------------\n'

        sub_title_2 = f'Bán {_category} đường {_street}, phường {_ward}, TP. Đà Lạt\n'
        sub_title_2 += sub_title_ext

        sub_title_3 = f'Bán {_category} giá hạt giẻ phường {_ward}, TP. Đà Lạt\n'
        sub_title_3 += sub_title_ext

        sub_title_3 = f'Chính chủ cần bán gấp {_category} giá hạt giẻ phường {_ward}, TP. Đà Lạt\n'
        sub_title_3 += sub_title_ext

        sub_title_4 = f'Cực HOT, phường {_ward}, TP. Đà Lạt\n'
        sub_title_4 += sub_title_ext

        sub_title_5 = f'GẤP!!! {_category} phường {_ward}, TP. Đà Lạt\n'
        sub_title_5 += sub_title_ext

        sub_titles = [sub_title_1, sub_title_2, sub_title_3, sub_title_4, sub_title_5]
        return self.rand(sub_titles)
    
    def init_body(self, _category, _ward, _street, _area, _price, _width, _construction, _function, _furniture, _buildingline, _legal, _description, _user_name, _phone_number, _icons):
        body_1 = ''
        body_1 += '🗺 Vị trí: đường {0}, phường {1}, TP. Đà Lạt\n'.format(_street, _ward)
    
        if _width != 'None':
            body_1 += '📏 Diện tích: {0} m2. Ngang: {1}m\n'.format(_area, _width)
        else:
            body_1 += '📏 Diện tích: {0} m2.\n'.format(_area)
        
        if _category != 'Đất':
            body_1 += '🏚 Kết cấu: {0}\n'.format(_construction)
            body_1 += '🛌 Công năng: {0}\n'.format(_function)
            body_1 += '📺 Nội thất: {0}\n'.format(_furniture)
        body_1 += '🚗 Lộ giới: {0}\n'.format(_buildingline)
        body_1 += '📝 Pháp lý: {0}\n'.format(_legal)
        body_1 += '{0} Mô tả: {1}\n'.format(self.rand(_icons) * 2, _description)
        body_1 += '{0} {1} gần ngay trung tâm, thuận tiện di chuyển, gần các tiện ích như: Chợ, trường học, bệnh viện. Khu vực an ninh, dân trí cao, thích hợp định cư lâu dài\n'.format(self.rand(_icons) * 2, _category,)
        body_1 += '💲 Giá: {0} tỷ - Thương lượng\n'.format(_price)
        body_1 += '☎ Liên hệ: {0} - {1}\n'.format(_phone_number, _user_name)

        body_2 = ''
        body_2 += 'Vị trí: đường {0}, phường {1}, TP. Đà Lạt\n'.format(_street, _ward)
    
        if _width != 'None':
            body_2 += 'Diện tích: {0} m2. Ngang: {1}m\n'.format(_area, _width)
        else:
            body_2 += 'Diện tích: {0} m2.\n'.format(_area)
        
        if _category != 'Đất':
            body_2 += 'Kết cấu: {0}\n'.format(_construction)
            body_2 += 'Công năng: {0}\n'.format(_function)
            body_2 += 'Nội thất: {0}\n'.format(_furniture)
        body_2 += 'Lộ giới: {0}\n'.format(_buildingline)
        body_2 += 'Pháp lý: {0}\n'.format(_legal)
        body_2 += f'Mô tả: {_description}\n'
        body_2 += f'{_category} gần ngay trung tâm, thuận tiện di chuyển, gần các tiện ích như: Chợ, trường học, bệnh viện. Khu vực an ninh, dân trí cao, thích hợp định cư lâu dài\n'
        body_2 += 'Giá: {0} tỷ - Thương lượng\n'.format(_price)
        body_2 += 'Liên hệ: {0} - {1}\n'.format(_phone_number, _user_name)

        body_3 = ''
        body_3 += f'- Diện tích: {_area}m2\n' 
        body_3 += f'- Pháp lý: {_legal}\n'
        if _category != 'Đất':
            body_3 += f'- Kết cấu: {_construction}. - {_function}\n'
        body_3 += f'{_buildingline}\n'
        body_3 += f'- Mô tả: {_description}\n'
        body_3 += f'- Giá: {_price} tỷ\n'
        body_3 += f'- Liên hệ: 0️⃣9️⃣6️⃣7️⃣2️⃣6️⃣7️⃣4️⃣3️⃣8️⃣ - Đ.Bình'

        body_4 = ''
        body_4 += f'- Diện tích: {_area}m2\n'
        body_4 += f'- Pháp lý: {_legal}\n'
        if _category != 'Đất':
            body_4 += f'- Kết cấu: {_construction}.\n'
            body_4 += f'- Gồm có: {_function}.\n'
        body_4 += f'{_buildingline}\n'
        body_4 += f'{_description}\n'
        body_4 += f'- Giá: {_price} tỷ\n'
        body_4 += f'- Liên hệ: 0️⃣9️⃣6️⃣7️⃣2️⃣6️⃣7️⃣4️⃣3️⃣8️⃣ - Đ.Bình'

        body_5 = ''
        if _category != 'Đất':
            body_5 += f'🍁🍁🍁 Cần bán nhà rất xinh xắn & ấm áp (nhà chính chủ)🍁🍁🍁\n'
            body_5 += f'🎁🎁 Nhà gồm: {_construction}. {_function}\n'
            body_5 += f'🎁🎁 Ưu điểm: {_description}\n'
            body_5 += f'🎁🎁 Phường {_ward} - TP. Đà Lạt\n'
            body_5 += f'🎁🎁 Thương lượng chính chủ\n'
            body_5 += f'🎁🎁 Liên hệ: {_phone_number}\n'

        body_6 = ''
        if _category != 'Đất':
            body_6 += f'Gia đình có căn nhà cần bán\n'
            body_6 += f'Kết cấu: {_construction}. {_function}\n'
            body_6 += f'{_buildingline}\n'
            body_6 += f'Ưu điểm: {_description}\n'
            body_6 += f'Phường {_ward} - TP. Đà Lạt\n'
            body_6 += f'- Giá: {_price} tỷ\n'
            body_6 += f'Liên hệ: {_phone_number}\n'

        body_7 = ''
        if _category != 'Đất':
            body_7 += f'{self.rand(_icons) * 3} Bán nhà nhà đẹp, xinh xắn gần trung tâm\n'
            body_7 += f'{self.rand(_icons) * 2} Diện tích: {_area}m2\n'
            body_7 += f'{self.rand(_icons) * 2} Kết cấu: {_construction}.\n'
            body_7 += f'{self.rand(_icons) * 2} Công năng: {_function}\n'
            body_7 += f'{self.rand(_icons) * 2} {_buildingline}\n'
            body_7 += f'{self.rand(_icons) * 2} Ưu điểm: {_description}\n'
            body_7 += f'{self.rand(_icons) * 2} Phường {_ward} - TP. Đà Lạt\n'
            body_7 += f'{self.rand(_icons) * 2} Giá: {_price} tỷ\n'
            body_7 += f'{self.rand(_icons) * 2} Liên hệ: 0️⃣9️⃣6️⃣7️⃣2️⃣6️⃣7️⃣4️⃣3️⃣8️⃣\n'

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

