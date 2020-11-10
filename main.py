import sqlite3
import sys

from PIL import Image
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QColorDialog, \
    QFileDialog, QLabel, QSlider


class BrushPoint:
    def __init__(self, x, y, color, size_brush):
        self.size_brush = size_brush
        self.x = x
        self.y = y
        self.colors = color

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(self.colors[0], self.colors[1], self.colors[-1])))
        painter.setPen(QColor(self.colors[0], self.colors[1], self.colors[-1]))
        painter.drawEllipse(self.x - self.size_brush, self.y - self.size_brush,
                            self.size_brush, self.size_brush)


class Eraser:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(QColor(240, 240, 240))
        painter.drawEllipse(self.x - 10, self.y - 10, 10, 10)


class Line:
    def __init__(self, x0, y0, x, y, color, size):
        self.size = size
        self.sx = x0
        self.sy = y0
        self.ex = x
        self.ey = y
        self.colors = color

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(self.colors[0], self.colors[1], self.colors[-1])))
        painter.setPen(QPen(QColor(self.colors[0], self.colors[1], self.colors[-1]),
                            self.size, Qt.SolidLine))
        painter.drawLine(self.sx, self.sy, self.ex, self.ey)


class Circle:
    def __init__(self, cx, cy, x, y, colors):
        self.cx = cx
        self.cy = cy
        self.x = x
        self.y = y
        self.colors = colors
        self.radius = 0

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(self.colors[0], self.colors[1], self.colors[-1])))
        painter.setPen(QColor(self.colors[0], self.colors[1], self.colors[-1]))
        self.radius = int(((self.cx - self.x) ** 2 + (self.cy - self.y) ** 2) ** 0.5)
        painter.drawEllipse(self.cx - self.radius, self.cy - self.radius, self.radius * 2,
                            self.radius * 2)


class Rectangle:
    def __init__(self, x0, y0, x, y, colors):
        self.cx = x0
        self.cy = y0
        self.x = x
        self.y = y
        self.colors = colors

    def draw(self, painter):
        painter.setBrush(QBrush(QColor(self.colors[0], self.colors[1], self.colors[-1])))
        painter.setPen(QColor(self.colors[0], self.colors[1], self.colors[-1]))
        painter.drawRect(self.cx, self.cy, self.x, self.y)


class Canvas(QWidget):
    def __init__(self):
        super(Canvas, self).__init__()

        self.color = '#000000'
        self.size_brush = 6
        self.size_line = 4
        self.id = 0
        self.red = 0
        self.green = 0
        self.blue = 0
        self.colors = (self.red, self.green, self.blue)
        self.id = 0

        self.file = sqlite3.connect('base.db')
        self.cur = self.file.cursor()

        self.objects = []

        self.instrument = 'brush'

        self.label = QLabel(self)
        self.label.move(0, 0)
        self.label.resize(949, 718)
        self.pixmap = QPixmap()
        self.label.setPixmap(self.pixmap)

        self.button = QPushButton(self)
        self.button.move(850, 5)
        self.button.setText('Цвет')
        self.button.clicked.connect(self.run)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        for obj in self.objects:
            obj.draw(painter)
        painter.end()

    def run(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.button.setStyleSheet(
                "background-color: {}".format(self.color))
            self.red = int(self.color[1:3], 16)
            self.green = int(self.color[3:5], 16)
            self.blue = int(self.color[5:], 16)
            self.colors = (self.red, self.green, self.blue)

    def mousePressEvent(self, event):
        self.id += 1
        if self.color not in list(map(lambda x: x[0],
                                      self.cur.execute("""SELECT color FROM colors""").fetchall())):
            self.cur.execute("""Insert INTO colors(color) Values (?) """, (self.color,))
        if self.instrument == 'brush':
            self.cur.execute("""Insert INTO Base_of_paint(action, color, size) Values 
            ('brush', (Select id from colors WHERE color = ?), ?) """,
                             (self.color, self.size_brush))
            self.objects.append(BrushPoint(event.x(), event.y(), self.colors,
                                           self.size_brush))
            self.update()
        elif self.instrument == 'line':
            self.cur.execute("""Insert INTO Base_of_paint(action, color, size) Values 
            ('line', (Select id from colors WHERE color = ?), ?) """,
                             (self.color, self.size_line,))
            self.objects.append(Line(event.x(), event.y(), event.x(), event.y(),
                                     self.colors, self.size_line))
            self.update()
        elif self.instrument == 'circle':
            self.cur.execute("""Insert INTO Base_of_paint(action, color) 
            Values ('circle', (Select id from colors WHERE color = ?)) """,
                             (self.color,))
            self.objects.append(Circle(event.x(), event.y(), event.x(), event.y(), self.colors))
            self.update()
        elif self.instrument == 'rectangle':
            self.cur.execute("""Insert INTO Base_of_paint(action, color) VALUES('rectangle', 
            (Select id from colors WHERE color = ?))""", (self.color,))
            self.objects.append(Rectangle(event.x(), event.y(), event.x(), event.y(),
                                          self.colors))
            self.update()
        elif self.instrument == 'eraser':
            self.cur.execute("""Insert INTO Base_of_paint(action, size) Values 
                        ('eraser', '6') """)
            self.objects.append(Eraser(event.x(), event.y()))
            self.update()
        self.file.commit()

    def mouseMoveEvent(self, event):
        if self.instrument == 'brush':
            self.objects.append(BrushPoint(event.x(), event.y(), self.colors, self.size_brush))
            self.update()
        elif self.instrument == 'line':
            self.objects[-1].ex = event.x()
            self.objects[-1].ey = event.y()
            self.update()
        elif self.instrument == 'circle':
            self.objects[-1].x = event.x()
            self.objects[-1].y = event.y()
            self.update()
        elif self.instrument == 'rectangle':
            self.objects[-1].x = event.x()
            self.objects[-1].y = event.y()
            self.update()
        elif self.instrument == 'eraser':
            self.objects.append(Eraser(event.x(), event.y()))
            self.update()

    def setBrush1(self):
        self.instrument = 'brush'
        self.size_brush = 2

    def setBrush2(self):
        self.instrument = 'brush'
        self.size_brush = 6

    def setBrush3(self):
        self.instrument = 'brush'
        self.size_brush = 10

    def setLine1(self):
        self.instrument = 'line'
        self.size_line = 2

    def setLine2(self):
        self.instrument = 'line'
        self.size_line = 3

    def setLine3(self):
        self.instrument = 'line'
        self.size_line = 4

    def setLine4(self):
        self.instrument = 'line'
        self.size_line = 5

    def setLine5(self):
        self.instrument = 'line'
        self.size_line = 6

    def setCircle(self):
        self.instrument = 'circle'

    def setRec(self):
        self.instrument = 'rectangle'

    def setPicture(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                                 'Картинка(*.jpg);; Картинка(*.png);; '
                                                 'Все файлы(*)')[0]
        if self.fname:
            self.image = Pictures(self.fname)
            self.image.show()

    def eraser(self):
        self.instrument = 'eraser'

    def save(self):
        save_file = QFileDialog.getSaveFileName(self, 'Загрузить картинку', '', '*.jpg;'
                                                                            ';*.png;;Все файлы *')
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.label.winId())
        if save_file[-1] == '*.jpg':
            screenshot.save(save_file[0], 'jpg')
        elif save_file[-1] == '*.png':
            screenshot.save(save_file[0], 'png')
        else:
            screenshot.save(save_file[0])
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('download', 
                                                ?)""", (save_file[0],))
        self.file.commit()


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi('window.ui', self)
        self.setCentralWidget(Canvas())

        self.action_brush1.triggered.connect(self.centralWidget().setBrush1)
        self.action_brush2.triggered.connect(self.centralWidget().setBrush2)
        self.action_brush3.triggered.connect(self.centralWidget().setBrush3)

        self.action_line1.triggered.connect(self.centralWidget().setLine1)
        self.action_line2.triggered.connect(self.centralWidget().setLine2)
        self.action_line3.triggered.connect(self.centralWidget().setLine3)
        self.action_line4.triggered.connect(self.centralWidget().setLine4)
        self.action_line5.triggered.connect(self.centralWidget().setLine5)

        self.action_circle.triggered.connect(self.centralWidget().setCircle)

        self.acnion_rectangle.triggered.connect(self.centralWidget().setRec)

        self.action_workpicture.triggered.connect(self.centralWidget().setPicture)

        self.action_lactic.triggered.connect(self.centralWidget().eraser)

        self.action_save.triggered.connect(self.centralWidget().save)

    def closeEvent(self, event):
        self.cur = self.centralWidget().file.cursor()
        self.cur.execute("""DELETE from Base_of_paint""")
        self.centralWidget().file.commit()
        self.centralWidget().file.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.centralWidget().save()
            elif event.key() == Qt.Key_D:
                self.centralWidget().instrument = 'circle'
            elif event.key() == Qt.Key_A:
                self.centralWidget().instrument = 'line'
                self.centralWidget().size_line = 4
            elif event.key() == Qt.Key_W:
                self.centralWidget().instrument = 'rectangle'
            elif event.key() == Qt.Key_Q:
                self.centralWidget().run()
            elif event.key() == Qt.Key_I:
                self.centralWidget().setPicture()
            elif event.key() == Qt.Key_L:
                self.centralWidget().instrument = 'eraser'
            elif event.key() == Qt.Key_E:
                self.centralWidget().instrument = 'brush'
                self.centralWidget().size_brush = 6


class Draw(QWidget):
    def __init__(self, fname):
        super().__init__()
        self.fname = fname

        self.pixmap = QPixmap(self.fname)
        self.image = QLabel(self)
        self.image.move(70, 10)
        self.image.setPixmap(self.pixmap)

        self.img = Image.open(self.fname)
        self.data = self.img.getdata()
        self.r = [(d[0], 0, 0) for d in self.data]
        self.g = [(0, d[1], 0) for d in self.data]
        self.b = [(0, 0, d[-1]) for d in self.data]
        self.all = [(d[0], d[1], d[-1]) for d in self.data]

        self.alpha = QSlider(self)
        self.alpha.move(30, 10)
        self.alpha.resize(20, 350)
        self.alpha.setMinimum(0)
        self.alpha.setMaximum(255)
        self.alpha.setValue(255)
        self.alpha.valueChanged.connect(self.change_alpha)

        self.file = sqlite3.connect('base.db')
        self.cur = self.file.cursor()

        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('download', ?)""",
                         (self.fname,))
        self.file.commit()

    def change_alpha(self):
        transport = int(self.alpha.value())
        self.img.putalpha(transport)
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('Change_alpha', ?)""",
                         (self.alpha.value(),))
        self.pixmap = QPixmap('picture.png')
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def red_channel(self):
        self.img.putdata(self.r)
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('red_channel', 
        'red')""")
        self.pixmap = QPixmap('picture.png')
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def green_channel(self):
        self.img.putdata(self.g)
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('green_channel', 
                                                                        'green')""")
        self.pixmap = QPixmap('picture.png')
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def blue_channel(self):
        self.img.putdata(self.b)
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('blue_channel', 
        'blue')""")
        self.pixmap = QPixmap('picture.png')
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def all_channel(self):
        try:
            self.img.putdata(self.all)
        except TypeError:
            self.img = Image.open('picture.png')
        finally:
            self.img.save('picture.png')
            self.pixmap = QPixmap('picture.png')
            self.image.setPixmap(self.pixmap)
            self.cur.execute("""Insert Into Base_of_picture(action, value) Values('all_channels', 
            'all')""")
            self.file.commit()

    def rotate_90(self):
        self.img = self.img.rotate(90, expand=True)
        x, y = self.img.size
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('rotate', 
                '90')""")
        self.pixmap = QPixmap('picture.png')
        self.image.resize(x, y)
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def inrotate_90(self):
        self.img = self.img.rotate(-90, expand=True)
        x, y = self.img.size
        self.img.save('picture.png')
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('rotate', 
                '-90')""")
        self.pixmap = QPixmap('picture.png')
        self.image.resize(x, y)
        self.image.setPixmap(self.pixmap)
        self.file.commit()

    def download(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                                 'Картинка(*.jpg);; Картинка(*.png);; '
                                                 'Все файлы(*)')[0]

        if self.fname:
            self.img = Image.open(self.fname)
            x, y = self.img.size
            self.image.resize(x, y)
            self.pixmap = QPixmap(self.fname)
            self.image.setPixmap(self.pixmap)
            self.data = self.img.getdata()
            self.r = [(d[0], 0, 0) for d in self.data]
            self.g = [(0, d[1], 0) for d in self.data]
            self.b = [(0, 0, d[-1]) for d in self.data]
            self.cur.execute("""Insert Into Base_of_picture(action, value) Values('download', 
                            ?)""", (self.fname,))
            self.file.commit()

    def save(self):
        save_file = QFileDialog.getSaveFileName(self, 'Загрузить картинку', '', '*.jpg;'
                                                                            ';*.png;;Все файлы *')
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.image.winId())
        if save_file[-1] == '*.jpg':
            screenshot.save(save_file[0], 'jpg')
        elif save_file[-1] == '*.png':
            screenshot.save(save_file[0], 'png')
        else:
            screenshot.save(save_file[0])
        self.cur.execute("""Insert Into Base_of_picture(action, value) Values('download', 
                                ?)""", (save_file[0],))
        self.file.commit()


class Pictures(QMainWindow):
    def __init__(self, fname):
        super(Pictures, self).__init__()
        uic.loadUi('pictures.ui', self)
        self.setCentralWidget(Draw(fname))

        self.action_red.triggered.connect(self.centralWidget().red_channel)
        self.action_green.triggered.connect(self.centralWidget().green_channel)
        self.action_blue.triggered.connect(self.centralWidget().blue_channel)
        self.action_all.triggered.connect(self.centralWidget().all_channel)

        self.action_rotate_90.triggered.connect(self.centralWidget().rotate_90)
        self.action_inrotate_90.triggered.connect(self.centralWidget().inrotate_90)

        self.action_download.triggered.connect(self.centralWidget().download)

        self.action_save.triggered.connect(self.centralWidget().save)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_A:
                self.centralWidget().inrotate_90()
            elif event.key() == Qt.Key_D:
                self.centralWidget().rotate_90()
            elif event.key() == Qt.Key_R:
                self.centralWidget().red_channel()
            elif event.key() == Qt.Key_G:
                self.centralWidget().green_channel()
            elif event.key() == Qt.Key_B:
                self.centralWidget().blue_channel()
            elif event.key() == Qt.Key_W:
                self.centralWidget().all_channel()
            elif event.key() == Qt.Key_I:
                self.centralWidget().download()
            elif event.key() == Qt.Key_S:
                self.centralWidget().save()

    def closeEvent(self, event):
        self.cur = self.centralWidget().file.cursor()
        self.cur.execute("""DELETE from Base_of_picture""")
        self.centralWidget().file.commit()
        self.centralWidget().file.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
