from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
    
    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        return len(self._data[0])
    
    def data(self, index, role = QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                value = self._data[index.row()][index.column()]
                return str(value)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            self._data[index.row()][index.column()] = value
            return True
        return False
    
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

class CustomProxyModel(QtCore.QSortFilterProxyModel):
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
            regex = QtCore.QRegExp(
                expresion, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp
            )
            if regex.indexIn(text) == -1:
                return False
        return True

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.table = QtWidgets.QTableView()

        self.centralWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout()

        self.field_search_1 = QtWidgets.QLineEdit()
        self.field_search_2 = QtWidgets.QLineEdit()

        self.field_search_1.textChanged.connect(self.on_lineEdit_textchanged_1)
        self.field_search_2.textChanged.connect(self.on_lineEdit_textchanged_2)

        data = [
            [123, 9, 2],
            [1, 0, -1],
            [3, 5, 2],
            [3, 3, 2],
            [5, 8, 9],
        ]

        self.load_site(data)
        

        # self.mainLayout.addWidget(self.)
        self.mainLayout.addWidget(self.table)
        self.mainLayout.addWidget(self.field_search_1)
        self.mainLayout.addWidget(self.field_search_2)

        self.centralWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.centralWidget)

    def load_site(self, data):
        self.model = TableModel(data)
        self.proxy = CustomProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)

    @QtCore.pyqtSlot(str)
    def on_lineEdit_textchanged_1(self, text):
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @QtCore.pyqtSlot(str)
    def on_lineEdit_textchanged_2(self, text):
        self.proxy.setFilterKeyColumn(2)
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()