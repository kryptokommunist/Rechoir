import sys
from PyQt5.QtWidgets import QApplication, QComboBox, QHBoxLayout, QPushButton, QSizePolicy, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import random
import pandas as pd
import numpy as np
import time

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def set_vl(self, pos):
        if self.vl:
            self.vl.remove()
        self.vl = self.axes.axvline(x=pos)
        self.draw()

    def plot(self, xdata, ydata, title):
        self.figure.delaxes(self.axes)
        self.axes = self.figure.add_subplot(111)
        self.axes.scatter(xdata, ydata, s=1)
        self.axes.set_title(title)
        self.vl = None
        self.draw()


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Rechoir'
        self.left = 100
        self.top = 100
        self.width = 2 * 640
        self.height = 2 * 480
        self.initData()
        self.initUI()

    def initData(self):
        self.data = pd.read_csv('~/Desktop/engine.data.csv', parse_dates=['DATETIME'])

    def play_sound(self):
        pass

    @pyqtSlot()
    def on_click(self):
        print('PyQt5 button click')
        data = self.currdata[0:10]
        for index, row in data.iterrows():
            self.play_sound()
            print(row['DATETIME'])
            for plt in self.plots:
                plt.set_vl(row['DATETIME'])

        
    def initUI(self):
        self.layout = QHBoxLayout()
        self.setWindowTitle(self.title)
        self.num_plots = 4
        self.cols = ['DT30', 'DP30', 'DN2', 'DFF']
        self.plots = []
        self.setGeometry(self.left, self.top, self.width, self.height)
        for i in range(self.num_plots):
            plot = PlotCanvas(self, width=10, height=2)
            plot.move(80, 10 + (200 * i))
            self.plots.append(plot)
        self.cb = QComboBox(self)
        self.cb.addItems([str(x) for x in self.data['ESN'].unique()])
        self.cb.currentIndexChanged.connect(self.selectionchange)
        self.cb.move(0,0)
        self.layout.addWidget(self.cb)
        self.selectionchange(0)
        self.play = QPushButton('Play', self)
        self.play.move(1100, 10)
        self.play.clicked.connect(self.on_click)
        self.show()

    def selectionchange(self,engine):
        print(self.cb.itemText(engine))
        self.currdata = self.data[self.data['ESN'] == int(self.cb.itemText(engine))].sort_values(by=['DATETIME'])
        for i, plt in enumerate(self.plots):
            plt.plot(self.currdata['DATETIME'], self.currdata[self.cols[i]], self.cols[i])

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())