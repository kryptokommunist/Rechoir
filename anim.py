from __future__ import unicode_literals
import sys
import os
import random
import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from sklearn import preprocessing
from pythonosc.udp_client import SimpleUDPClient
from PyQt5.QtWidgets import QComboBox, QPushButton

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

DELAY = 10
OSC_PORT = 57120
OSC_IP = "127.0.0.1"

client = SimpleUDPClient(OSC_IP, OSC_PORT)

def send_osc(input_data):
    """
    Send input via OSC
    """
    client.send_message("/sound", input_data)

def normalize_data(data_input):
    """
    Normalize data to values between 1 and 0 based on
    min and max val
    """
    x = data_input.values #returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    data_input = pd.DataFrame(x_scaled)
    return data_input

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        self.xdata = None
        self.ydata = None
        self.line_pos = 0
        timer.start(DELAY)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        
        self.axes.cla()
        self.axes.scatter(self.xdata, self.ydata, 1)
        self.axes.axvline(x=self.xdata.iloc[self.line_pos])
        self.draw()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.initData()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.cb = QComboBox(self)
        self.cb.addItems([str(x) for x in self.data['ESN'].unique()])
        self.cb.currentIndexChanged.connect(self.selectionchange)
        self.cb.move(0,0)
        self.help_menu.addAction('&About', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        l.addWidget(self.cb)
        self.plots = []
        for i in range(4):
            dc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
            l.addWidget(dc)
            self.plots.append(dc)
        self.play = QPushButton('Play', self)
        l.addWidget(self.play)
        self.play.clicked.connect(self.on_click)
        timer = QtCore.QTimer(self)
        self.playing = False
        timer.timeout.connect(self.loop)
        self.selectionchange(0)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        timer.start(DELAY)
        self.statusBar().showMessage("All hail matplotlib!", 2000)

    def selectionchange(self,engine):
        data = self.data[self.data['ESN'] == int(self.cb.itemText(engine))].sort_values(by=['DATETIME'])
        data = data[(data['DATETIME'] > '2037-06-01') & (data['DATETIME'] < '2038-02-01')]
        self.normalized_data = normalize_data(data[["ESN", "P0", "P2", "OP", "DN1", "DTGT", "DFF", "DT30", "DFF"]])

        cols = ['DT30', 'DP30', 'DN2', 'DFF']
        for i, plt in enumerate(self.plots):
            plt.xdata = data['DATETIME']
            plt.ydata = data[cols[i]]
            plt.line_pos = 0

    def loop(self):
        if self.playing:
            for plt in self.plots:
                plt.line_pos += 1
            send_osc(list(self.normalized_data.iloc[self.plots[0].line_pos]))
                

    def on_click(self):
        print('click')
        self.playing = not self.playing
                
                      
    def initData(self):
        self.data = pd.read_csv('~/Desktop/engine.data.csv', parse_dates=['DATETIME'])

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """embedding_in_qt5.py example
Copyright 2005 Florent Rougon, 2006 Darren Dale, 2015 Jens H Nielsen

This program is a simple example of a Qt5 application embedding matplotlib
canvases.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation.

This is modified from the embedding in qt4 example to show the difference
between qt4 and qt5"""
                                )


qApp = QtWidgets.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()