from PyQt5 import QtGui, QtSql, QtCore, QtWidgets
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage, QPainter, QBrush, QPen
from PyQt5.QtWidgets import *
import sys
import sqlite3
import os
import datetime


class Window(QtWidgets.QMainWindow):
    def __init__(self, filePath=None):
        super().__init__()
        self.init_ui()


        self.line_start = None
        self.line_end = None
        self.lines = list()
        self.arrow = False
        self.drawing = True
        self.brushSize = 2
        self._clear_size = 20
        self.brushColor = QtGui.QColor(Qt.black)
        self.lastPoint = QtCore.QPoint()
        self.eraser = False

    def init_ui(self):
        self.setWindowTitle("Paint")
        self.setGeometry(400, 400, 1000, 600)
        self.image = QtGui.QImage(self.size(), QtGui.QImage.Format_ARGB32)
        self.image.fill(Qt.white)
        self.imageDraw = QtGui.QImage(self.size(), QtGui.QImage.Format_ARGB32)
        self.imageDraw.fill(Qt.transparent)

        # панель
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("File")
        b_size = mainMenu.addMenu("Size")
        b_color = mainMenu.addMenu("Color")
        shapes = mainMenu.addMenu("Tools")

        # история
        fileHistoryAction = QAction("History    'Ctrl + h'", self)
        fileHistoryAction.setShortcut("Ctrl + O")
        fileMenu.addAction(fileHistoryAction)
        fileHistoryAction.triggered.connect(self.fileHistory)

        # открытие
        openAction = QAction("Open    'Ctrl + O'", self)
        openAction.setShortcut("Ctrl + O")
        fileMenu.addAction(openAction)
        openAction.triggered.connect(self.openfile)

        # сохранение
        saveAction = QAction("Save    'Ctrl + S'", self)
        saveAction.setShortcut("Ctrl + S")
        fileMenu.addAction(saveAction)
        saveAction.triggered.connect(self.save)

        # очистка
        clearAction = QAction("Clear    'Ctrl + C'", self)
        clearAction.setShortcut("Ctrl + C")
        fileMenu.addAction(clearAction)
        clearAction.triggered.connect(self.clear)

        # размер кисти
        pix_4 = QAction("4px", self)
        b_size.addAction(pix_4)
        pix_4.triggered.connect(self.Pixel_4)
        pix_7 = QAction("7px", self)
        b_size.addAction(pix_7)
        pix_7.triggered.connect(self.Pixel_7)
        pix_9 = QAction("9px", self)
        b_size.addAction(pix_9)
        pix_9.triggered.connect(self.Pixel_9)
        pix_12 = QAction("12px", self)
        b_size.addAction(pix_12)
        pix_12.triggered.connect(self.Pixel_12)

        # цвета
        black = QAction("Black", self)
        b_color.addAction(black)
        black.triggered.connect(self.blackColor)
        white = QAction("White", self)
        b_color.addAction(white)
        white.triggered.connect(self.whiteColor)
        green = QAction("Green", self)
        b_color.addAction(green)
        green.triggered.connect(self.greenColor)
        yellow = QAction("Yellow", self)
        b_color.addAction(yellow)
        yellow.triggered.connect(self.yellowColor)
        red = QAction("Red", self)
        b_color.addAction(red)
        red.triggered.connect(self.redColor)

        # фигуры
        brush = QAction("Brush", self)
        shapes.addAction(brush)
        brush.triggered.connect(self.brushToggle)
        arrow = QAction("Arrow", self)
        shapes.addAction(arrow)
        arrow.triggered.connect(self.arrowToggle)

    def mousePressEvent(self, event):
        self.line_start = (event.x(), event.y())
        if event.button() == Qt.LeftButton:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.eraser = False
            self.lastPoint = event.pos()
        elif event.button() == Qt.RightButton:
            self.eraser = True
            pixmap = QtGui.QPixmap(QtCore.QSize(1, 1) * self._clear_size)
            pixmap.fill(Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QPen(Qt.black, 2))
            painter.drawRect(pixmap.rect())
            painter.end()
            cursor = QtGui.QCursor(pixmap)
            QtWidgets.QApplication.setOverrideCursor(cursor)

    def mouseMoveEvent(self, event):
        self.line_end = (event.x(), event.y())
        if event.button() == 0 and self.drawing:
            painter = QtGui.QPainter(self.imageDraw)
            painter.setPen(QtGui.QPen(self.brushColor, self.brushSize, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            if self.eraser:
                r = QtCore.QRect(QtCore.QPoint(), self._clear_size * QtCore.QSize())
                r.moveCenter(event.pos())
                painter.save()
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                painter.eraseRect(r)
                painter.restore()
            else:
                painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.arrow:
            self.lines.append((self.line_start, self.line_end))
        self.line_start = None
        if event.button == QtCore.Qt.LeftButton:
            self.drawing = False
        self.repaint()

    def paintEvent(self, event):
        canvasPainter = QtGui.QPainter(self)
        canvasPainter.begin(self)
        if self.arrow:
            for line in self.lines:
                drawArrow(QtGui.QPainter(self.imageDraw), line[0], line[1])

        canvasPainter.drawImage(self.rect(), self.image, self.image.rect())
        canvasPainter.drawImage(self.rect(), self.imageDraw, self.imageDraw.rect())
        canvasPainter.end()

    # открытие
    def openfile(self):
        self.filePath, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                                       "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
        if self.filePath == "":
            return
        self.image = (QImage(self.filePath).size(), QtGui.QImage.Format_ARGB32)
        self.image = QImage(self.filePath)
        self.imageDraw = QtGui.QImage(self.size(), QtGui.QImage.Format_ARGB32)
        self.imageDraw.fill(QtCore.Qt.transparent)
        self.update()

    # сохранение
    def save(self):
        try:
            for x in range(self.imageDraw.width()):
                for y in range(self.imageDraw.height()):
                    if self.imageDraw.pixel(x, y) != 0:
                        if self.imageDraw.pixel(x, y) == 4278190080:
                            self.image.setPixelColor(x, y, Qt.black)
                        if self.imageDraw.pixel(x, y) == 4278255360:
                            self.image.setPixelColor(x, y, Qt.green)
                        if self.imageDraw.pixel(x, y) == 4294967295:
                            self.image.setPixelColor(x, y, Qt.white)
                        if self.imageDraw.pixel(x, y) == 4294967040:
                            self.image.setPixelColor(x, y, Qt.yellow)
                        if self.imageDraw.pixel(x, y) == 4294901760:
                            self.image.setPixelColor(x, y, Qt.red)
            self.filePath, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                           "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
            if self.filePath == "":
                return
            self.image.save(self.filePath)
            size = os.path.getsize(self.filePath)
            name = os.path.basename(self.filePath)
            self.dt = datetime.datetime
            with sqlite3.connect('fileHistory.db') as con:
                cur = con.cursor()

                query = f'INSERT INTO history(name,dir,size,datetime) VALUES(?, ?, ?, ?)'
                cur.execute(query, (name, self.filePath, size, f'{self.dt.year}-{self.dt.month}-{self.dt.day} {self.dt.hour}:{self.dt.minute}:{self.dt.second}'))
                con.commit()
        except Exception as e:
            print(e)

    # очистка
    def clear(self):
        self.imageDraw.fill(Qt.transparent)
        self.update()

    # размер кисти
    def Pixel_4(self):
        self.eraser = False
        self.brushSize = 4

    def Pixel_7(self):
        self.eraser = False
        self.brushSize = 7

    def Pixel_9(self):
        self.eraser = False
        self.brushSize = 9

    def Pixel_12(self):
        self.eraser = False
        self.brushSize = 12

    # цвета
    def blackColor(self):
        self.brushColor = Qt.black

    def whiteColor(self):
        self.brushColor = Qt.white

    def greenColor(self):
        self.brushColor = Qt.green

    def yellowColor(self):
        self.brushColor = Qt.yellow

    def redColor(self):
        self.brushColor = Qt.red

    # история файлов
    def fileHistory(self):
        try:
            self.second_form = History()
            self.second_form.show()
        except Exception as e:
            print(e)

    # инструменты
    def arrowToggle(self):
        self.drawing = False
        self.arrow = True

    def brushToggle(self):
        self.drawing = True
        self.arrow = False


# отрисовка стрелки
def drawArrow(qp, p1, p2):
    qp.drawLine(*p1, *p2)
    line_vec = (p2[0] - p1[0], p2[1] - p1[1])
    line_len = (line_vec[0] ** 2 + line_vec[1] ** 2) ** 0.5
    if line_len == 0:
        return
    x = line_len / 5
    c = x / 2 ** 0.5
    p_line_vec = (-line_vec[1] / line_len * c, line_vec[0] / line_len * c)
    p3 = (line_vec[0] - line_vec[0] / line_len * c + p_line_vec[0] + p1[0], line_vec[1] - line_vec[1] / line_len * c + p_line_vec[1] + p1[1])
    p4 = (line_vec[0] - line_vec[0] / line_len * c - p_line_vec[0] + p1[0], line_vec[1] - line_vec[1] / line_len * c - p_line_vec[1] + p1[1])
    qp.drawLine(*p2, *map(round, p3))
    qp.drawLine(*p2, *map(round, p4))



# окно истории файлов
class History(QtWidgets.QWidget):
    def __init__(self, *args):
        super().__init__()
        self.init_ui(self)
        self.con = sqlite3.connect("fileHistory.db")
        self.cur = self.con.cursor()
        self.res = self.cur.execute('''SELECT * FROM history''').fetchall()

    def init_ui(self, args):
        self.setGeometry(600, 250, 600, 250)
        self.setWindowTitle('File History')
        self.setStyleSheet("background-color: white;")

        self.tableWidget = QtWidgets.QTableWidget(8, 4, self)
        self.tableWidget.setHorizontalHeaderLabels(['name', 'directory', 'size(bytes)', 'date'])
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setGeometry(0, 0, 600, 250)



        for i, row in enumerate(self.res):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))





app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())