import json
FILE_CONFIG = 'c:\\Users\\dinhb\\Desktop\\ItemManagement\\static\\config.json'

from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QGridLayout,
    QMessageBox,
    QProgressBar,
    QVBoxLayout
)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal

from management.exe.execute import ExecuteOnDesktop
from management.exe.GoogleDriveAPI import GoogleDrive
from management.exe.GoogleSheetAPI import GoogleSheet


class ListBoxImages(QListWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        
            links = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
                else:
                    links.append(str(url.toString()))
            self.addItems(links)

        else:
            event.ignore()

class InputSection(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.l_main = QVBoxLayout()
        self.l_input = QGridLayout()

        lCategory = QLabel('Danh mục')
        # lCategory.setFixedWidth(120)
        self.iCategory = QComboBox()
        self.iCategory.addItem('Nhà')
        self.iCategory.addItem('Đất')
        self.iCategory.addItem('Villa')
        self.iCategory.addItem('Khách sạn')

        lRoad = QLabel('Đường')
        lWard = QLabel('Phường')
        self.iRoad = QLineEdit()
        self.iWard = QLineEdit()
        # self.iWard.setFixedWidth(30)

        lArea = QLabel('Diện tích')
        lWidth = QLabel('Ngang')
        self.iArea = QLineEdit()
        self.iArea.setPlaceholderText('m2')
        self.iWidth = QLineEdit()
        self.iWidth.setPlaceholderText('m')

        lConstruction = QLabel('Kết cấu')
        self.iConstruction = QLineEdit('1 trệt, ')
        # self.iConstruction.setPlaceholderText('Tầng')

        lFunction = QLabel('Công năng')
        self.iFunction = QLineEdit('1 PK, 1 bếp, ')
        # self.iFunction.setPlaceholderText('PK, PN, Bếp, ...')

        lFuriture = QLabel('Nội thất')
        lFuriture.setFixedWidth(90)
        self.iFurniture = QComboBox()
        self.iFurniture.addItem('Không')
        self.iFurniture.addItem('Nội thất cơ bản')
        self.iFurniture.addItem('Nội thất cao cấp')

        lBuildingLine = QLabel('Lộ giới')
        self.iBuildingLine = QComboBox()
        self.iBuildingLine.addItem('Đường xe máy')
        self.iBuildingLine.addItem('Đường xe hơi')
        self.iBuildingLine.addItem('Mặt tiền đường')
        self.iBuildingLine.setCurrentIndex(1)

        lLegal = QLabel('Pháp lý')
        self.iLegal = QComboBox()
        self.iLegal.addItem('Sổ nông nghiệp')
        self.iLegal.addItem('Sổ xây dựng')
        self.iLegal.addItem('Sổ riêng xây dựng')
        self.iLegal.setCurrentIndex(2)

        lDescription = QLabel('Mô tả')
        self.iDescription = QTextEdit()
        self.iDescription.setFixedHeight(200)

        lPrice = QLabel('Giá')
        self.iPrice = QLineEdit()
        self.iPrice.setPlaceholderText('tỷ')

        lContact = QLabel('Liên hệ')
        self.iContact = QLineEdit()
        with open(FILE_CONFIG, encoding='utf8') as json_file:
            data = json.load(json_file)
        user_phone = data['user_info']['phone_number']
        self.iContact.setText(user_phone)

        lNote = QLabel('Ghi chú')
        self.iNote = QTextEdit()
        self.iNote.setFixedHeight(100)

        self.btn_clear = QPushButton('Clear')
        self.btn_save = QPushButton('Save')

        self.w_progress = QProgressBar()
        self.w_progress.setRange(0, 12)

        self.l_input.addWidget(lCategory, 0, 0)
        self.l_input.addWidget(self.iCategory, 0, 1, 1, 3)
        self.l_input.addWidget(lRoad, 1, 0)
        self.l_input.addWidget(self.iRoad, 1, 1)
        self.l_input.addWidget(lWard, 1, 2)
        self.l_input.addWidget(self.iWard, 1, 3)
        self.l_input.addWidget(lArea, 2, 0)
        self.l_input.addWidget(self.iArea, 2, 1)
        self.l_input.addWidget(lWidth, 2, 2)
        self.l_input.addWidget(self.iWidth, 2, 3)
        self.l_input.addWidget(lConstruction, 3, 0)
        self.l_input.addWidget(self.iConstruction, 3, 1)
        self.l_input.addWidget(lFunction, 3, 2)
        self.l_input.addWidget(self.iFunction, 3, 3)
        self.l_input.addWidget(lFuriture, 4, 0)
        self.l_input.addWidget(self.iFurniture, 4, 1)
        self.l_input.addWidget(lBuildingLine, 4, 2)
        self.l_input.addWidget(self.iBuildingLine, 4, 3)
        self.l_input.addWidget(lLegal, 5, 0)
        self.l_input.addWidget(self.iLegal, 5, 1, 1, 3)
        self.l_input.addWidget(lDescription, 6, 0)
        self.l_input.addWidget(self.iDescription, 6, 1, 1, 3)
        self.l_input.addWidget(lPrice, 7, 0)
        self.l_input.addWidget(self.iPrice, 7, 1, 1, 3)
        self.l_input.addWidget(lContact, 8, 0)
        self.l_input.addWidget(self.iContact, 8, 1, 1, 3)
        self.l_input.addWidget(lNote, 9, 0)
        self.l_input.addWidget(self.iNote, 9, 1, 1, 3)
        self.l_input.addWidget(self.btn_clear, 10, 0)
        self.l_input.addWidget(self.btn_save, 10, 1, 1, 3)

        # self.l_input.addWidget(self.w_progress, Qt.AlignCenter)

        self.l_main.addLayout(self.l_input)
        self.l_main.addWidget(self.w_progress)
        self.setLayout(self.l_main)

    def getValue(self):
        info = []
        if self.iWidth.text() == '':
            self.iWidth.setText('None')
        # self.iBuildingLine.currentText = self.iBuildingLine.currentText() == ''?
        
        if self.iCategory.currentIndex() == 1:
            info.append(self.iCategory.currentText())
            info.append(self.iWard.text())
            info.append(self.iRoad.text())
            info.append(self.iArea.text())
            info.append(self.iPrice.text())
            info.append(self.iWidth.text())
            info.append('None')
            info.append('None')
            info.append('None')
            info.append(self.iBuildingLine.currentText())
            info.append(self.iLegal.currentText())
            info.append(self.iDescription.toPlainText())
            info.append(self.iNote.toPlainText())

        else:
            info.append(self.iCategory.currentText())
            info.append(self.iWard.text())
            info.append(self.iRoad.text())
            info.append(self.iArea.text())
            info.append(self.iPrice.text())
            info.append(self.iWidth.text())
            info.append(self.iConstruction.text())
            info.append(self.iFunction.text())
            info.append(self.iFurniture.currentText())
            info.append(self.iBuildingLine.currentText())
            info.append(self.iLegal.currentText())
            info.append(self.iDescription.toPlainText())
            info.append(self.iNote.toPlainText())
        return info

class ImageSection(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        mainLayout = QGridLayout()
        self.lsbox_1 = ListBoxImages()
        lLsBox_1 = QLabel('Hình ảnh')
        self.lsbox_2 = ListBoxImages()
        lLsBox_2 = QLabel('Hình sổ')

        mainLayout.addWidget(lLsBox_1, 0, 0)
        mainLayout.addWidget(self.lsbox_1, 0, 1, 1, 4)
        mainLayout.addWidget(lLsBox_2, 1, 0)
        mainLayout.addWidget(self.lsbox_2, 1, 1, 1, 4)
        self.setLayout(mainLayout)
         
class TabCreateItem(QWidget):
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
        self.lsbox_images = ImageSection()
        self.inputsection = InputSection()
        self.mainLayout.addWidget(self.lsbox_images)
        self.mainLayout.addWidget(self.inputsection)
        self.setLayout(self.mainLayout)

        self.result = None

        self.inputsection.btn_save.clicked.connect(lambda : self.handleOnDesktop())
        self.inputsection.btn_save.clicked.connect(lambda : self.handelOnDrive())
        self.inputsection.btn_clear.clicked.connect(lambda: self.handleClearBtn())

    def messagePopup(self, message):
        msg = QMessageBox()
        msg.setWindowTitle('Message')
        msg.setText(message)

        msg.exec()
        pass
    
    def handleOnDesktop(self):
        e_desktop = ExecuteOnDesktop()
        self.iValue = [e_desktop.handleDate()]
        self.iValue += self.inputsection.getValue()
        iImages_1 = []
        iImages_2 = []
        for i in range(self.lsbox_images.lsbox_1.count()):
            iImages_1.append(self.lsbox_images.lsbox_1.item(i).text())
        for i in range(self.lsbox_images.lsbox_2.count()):
            iImages_2.append(self.lsbox_images.lsbox_2.item(i).text())
        
        for i in self.iValue:
            if i == '':
                self.messagePopup('Not enough info')
                return False
        if len(iImages_1) < 1:
            self.messagePopup('Images field is requirement')
            return False
        self.result = e_desktop.copyFile([self.iValue[0], self.iValue[1], self.iValue[2], self.iValue[3], self.iValue[4], self.iValue[5]], iImages_1)

    def handelOnDrive(self):
        self.thread = QThread()
        self.worker_upload = ThreadUpload(self.result, self.iValue)

        self.worker_upload.moveToThread(self.thread)

        self.thread.started.connect(self.worker_upload.upload)
        
        self.worker_upload.process.connect(self.reportProgress)

        self.worker_upload.finished.connect(self.worker_upload.deleteLater)
        self.worker_upload.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.inputsection.btn_save.setEnabled(False)
        self.thread.finished.connect(lambda : self.inputsection.btn_save.setEnabled(True))
        
        pass

    def handleClearBtn(self):
        self.lsbox_images.lsbox_1.clear()
        self.lsbox_images.lsbox_2.clear()

        self.inputsection.iWard.setText('')
        self.inputsection.iRoad.setText('')
        self.inputsection.iArea.setText('')
        self.inputsection.iPrice.setText('')
        self.inputsection.iWidth.setText('')
        self.inputsection.iConstruction.setText('')
        self.inputsection.iFunction.setText('')
        self.inputsection.iDescription.setPlainText('')
        self.inputsection.iNote.setPlainText('')

    def reportProgress(self, n):
        self.inputsection.w_progress.setValue(n)
        pass

class ThreadUpload(QObject):
    process = pyqtSignal(int)
    finished = pyqtSignal()
    def __init__(self, result, value, parent = None):
        super().__init__(parent)
        self.result = result
        self.value = value

    def upload(self):
        step = 1
        if self.result:
            ls_img = self.result['image_list']
            step += 1
            self.process.emit(step)

            folder_name = self.result['folder_name']
            step += 1
            self.process.emit(step)

            e_drive = GoogleDrive()
            step += 1
            self.process.emit(step)

            response = e_drive._upload(folder_name, ls_img) #{id, folder_name}
            step += 1
            self.process.emit(step)

            ls_nameimage = ''
            step += 1
            self.process.emit(step)

            ls_idimage = ''
            step += 1
            self.process.emit(step)

            for i in response:
                ls_nameimage += i['name'] + '|'
                ls_idimage += i['id'] + '|'
            
            self.value.append(response[0]['parents'][0])
            step += 1
            self.process.emit(step)

            self.value.append(ls_nameimage)
            step += 1
            self.process.emit(step)

            self.value.append(ls_idimage)
            step += 1
            self.process.emit(step)

            e_spreadsheet = GoogleSheet()
            step += 1
            self.process.emit(step)

            e_spreadsheet._append(e_spreadsheet.spread_id, self.value)
            step += 1
            self.process.emit(step)

        self.finished.emit()