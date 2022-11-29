import sys
import os
from management.UI.tab_createItem import TabCreateItem
from management.UI.tab_autoInit import TabAutoInit

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QListWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QTextEdit, QGridLayout, QListWidgetItem, QTabWidget

class App(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.tab_widget = TabWidget()
        self.setCentralWidget(self.tab_widget)

        self.show()


class TabWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        mainLayout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab_1 = TabCreateItem()
        self.tab_2 = TabAutoInit()


        self.tabs.addTab(self.tab_1, 'Create')
        self.tabs.addTab(self.tab_2, 'Content')

        self.tabs.setCurrentIndex(0)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)

def main():
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())