# Importing Packages
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import pyqtgraph as pg
import sounddevice as sd
import testGUI as ss
from helpers import *
from popupWindow import Ui_OtherWindow


class loaderThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super(loaderThread, self).__init__()
        self.filepath = ...
        self.file = ...

    def run(self):
        self.file = loadAudioFile(self.filepath)
        self.signal.emit(self.file)


class equalizerApp(ss.Ui_MainWindow):
    # Window Mode
    windowMode = "Rectangle"

    def __init__(self, starterWindow):
        """
        Main loop of the UI
        :param mainWindow: QMainWindow Object
        """
        super(equalizerApp, self).setupUi(starterWindow)

        # Set Main View
        self.tabWidget.setCurrentIndex(0)

        # Setup popup Window
        self.popup_window = QtWidgets.QMainWindow()
        self.pop_ui = Ui_OtherWindow()
        self.pop_ui.setupUi(self.popup_window)

        # Initializations
        self.signalFile = ...  # the file loaded ---> data, Sampling Rate
        self.signalDataType = ...  # contains the data type of the signal
        self.signalFourier = ...  # fourier transform of the signal file data
        self.signalBands = ...  # Contains the signal bands
        self.signalBandsCopy = ...  # contains a copy of the signal bands for modification purposes
        self.signalModification = ...  # Contains the signal with the modified data
        self.signalModificationInv = ...  # Contains the data to be played and writen to wave
        self.filename = ...  # contains the file path
        self.format = ...  # contains the file format
        self.loadThread = loaderThread()  # contains the loader thread
        self.sliderValuesClicked = {0:..., 1:..., 2:..., 3:..., 4:..., 5:..., 6:..., 7:..., 8:..., 9:...}  # list contains the last pressed values
        self.results = {1:[], 2:[]}
        self.resultCounter = 1

        # encapsulations
        self.sliders = [self.verticalSlider, self.verticalSlider_2, self.verticalSlider_3, self.verticalSlider_4,
                        self.verticalSlider_5, self.verticalSlider_6, self.verticalSlider_7, self.verticalSlider_8,
                        self.verticalSlider_9, self.verticalSlider_10]

        self.playerButtons = [self.playButton, self.stopButton]
        self.windows = [self.rectangle, self.hanning, self.hamming]
        self.frontWidgets = [self.inputSignalGraph, self.sliderChangedGraph]
        self.outputWidgets = [self.inputTimeOriginal, self.outputTimeModified, self.inputFourierOriginal, self.outputFourierModified]
        # self.differenceWidgets = [self.TimeDifference, self.FourierDifference]
        self.compareWidgets = [self.result1Plot, self.result2Plot]
        self.differenceWidgets = [self.pop_ui.timeDifference, self.pop_ui.fourierDifference]

        self.outputButtons = [self.resetBands, self.showResult, self.playResult]
        self.saveButtons = [self.saveFile_btn, self.showDifference_btn, self.saveResult_btn, self.compareResult_btn]

        # Top Titles
        self.widgetTitles = ["Original Signal", "Changes Applied"]
        self.outputWidgetsTitles = ["Original Signal in Time", "Output Signal in Time", "Original Signal Fourier", "Output Signal Fourier"]
        self.compareTitles = ["First Result", "Second Result"]
        self.differenceTitles = ["Time Difference", "Fourier Difference"]

        # Bottom Titles
        self.widgetsBottomLabels = ["No. of Samples", "Frequencies"]
        self.outputWidgetsBottomLabels = ["No. of Samples", "No. of Samples", "Frequencies", "Frequencies"]
        self.compareTitles = ["Frequencies", "Frequencies"]


        # pens configurations (Plot Colors)
        self.pens = [pg.mkPen(color=(255, 0, 0)), pg.mkPen(color=(0, 255, 0)),
                     pg.mkPen(color=(0, 0, 255)), pg.mkPen(color=(200, 87, 125)),
                     pg.mkPen(color=(123, 34, 203))]

        # Setup widget configurations
        for widget in self.frontWidgets:
            widget.plotItem.setTitle(self.widgetTitles[self.frontWidgets.index(widget)])
            widget.plotItem.showGrid(True, True, alpha=0.8)
            widget.plotItem.setLabel("bottom", text=self.widgetsBottomLabels[self.frontWidgets.index(widget)])

        for widget in self.outputWidgets:
            widget.plotItem.setTitle(self.outputWidgetsTitles[self.outputWidgets.index(widget)])
            widget.plotItem.showGrid(True, True, alpha=0.8)
            widget.plotItem.setLabel("bottom", text=self.outputWidgetsBottomLabels[self.outputWidgets.index(widget)])


        for widget in self.compareWidgets:
            widget.plotItem.setTitle(self.compareTitles[self.compareWidgets.index(widget)])
            widget.plotItem.showGrid(True, True, alpha=0.8)
            widget.plotItem.setLabel("bottom", text=self.compareTitles[self.compareWidgets.index(widget)])


        for widget in self.differenceWidgets:
            widget.plotItem.setTitle(self.differenceTitles[self.differenceWidgets.index(widget)])
            widget.plotItem.showGrid(True, True, alpha=0.8)
            widget.plotItem.setLabel("bottom", text=self.widgetsBottomLabels[self.differenceWidgets.index(widget)])

        # CONNECTIONS
        self.actionload.triggered.connect(self.loadFile)
        for slider in self.sliders:
            slider.id = self.sliders.index(slider)
            slider.signal.connect(self.sliderChanged)

        self.playButton.clicked.connect(lambda : sd.play(self.signalFile["data"] ,  self.signalFile['frequency']))
        self.stopButton.clicked.connect(lambda : sd.stop())
        self.playResult.clicked.connect(lambda : sd.play(self.signalModificationInv.astype(self.signalDataType), self.signalFile['frequency']))
        self.resetBands.clicked.connect(self.resetAllBands)

        # Save Output Buttons
        self.showResult.clicked.connect(self.showResultOutput)
        self.saveFile_btn.clicked.connect(lambda: self.saveWaveFile('results/outputFile.wav', self.signalFile['frequency'], self.signalModificationInv))

        # Difference Button
        self.showDifference_btn.clicked.connect(self.showDifferenceWindow)

        #Compare Results
        self.saveResult_btn.clicked.connect(self.saveResult)
        self.compareResult_btn.clicked.connect(self.compareResults)



    def loadFile(self):
        """
        Load the File from User and add it to files dictionary
        :return:
        """
        # Open File
        self.filename, self.format = QtWidgets.QFileDialog.getOpenFileName(None, "Load Signal", "/home",
                                                                           "*.wav;;")
        # check if file not loaded (cancel loading....etc.)
        if self.filename == "":
            pass
        else:
            self.loadThread.filepath = self.filename
            self.loadThread.start()
            self.loadThread.signal.connect(self.loadFileConfiguration)
            for btn in zip(self.playerButtons, self.outputButtons):
                btn[0].setEnabled(True)
                btn[1].setEnabled(True)

            self.outputButtons[2].setEnabled(True)

    def loadFileConfiguration(self, fileName):
        """
        takes the file from loadFile and plot the fourier transform of the signal and the original signal
        :param fileName: file path ... string
        :return: none
        """
        self.signalFile = fileName
        self.signalModificationInv = self.signalFile['data']
        self.signalDataType = self.signalFile['data'].dtype
        self.plotSignalLoaded()

    def plotSignalLoaded(self):
        """
        used by loadFileConfiguration to plot the signal
        :return: none
        """
        self.signalFourier = fourierTransform(self.signalFile)
        self.signalBands = createBands(self.signalFourier)
        self.signalBandsCopy = np.copy(self.signalBands)

        # on loading a new file
        for widget in self.frontWidgets:
            widget.plotItem.clear()
        self.plotUsingDimension()

    def plotUsingDimension(self):
        """
        used to plot the data from the specified fourier attribute to the specified graph
        :return: none
        """
       # check the dimensions of the signal and plot using best method
        try:
            if len(self.signalFile['dim']) == 2 :
                self.inputSignalGraph.plotItem.plot(self.signalFile['data'][:, 0], pem=self.pens[0]) # if 2d print one channel
                self.plotFourier(self.sliderChangedGraph, self.signalFourier['transformedData'][:, 0], pen=self.pens[1])
            else:
                # plotting
                self.inputSignalGraph.plotItem.plot(self.signalFile['data'], pem=self.pens[0])
                self.plotFourier(self.sliderChangedGraph, self.signalFourier['transformedData'], pen=self.pens[1])
        except:
            pass


    def sliderChanged(self, indx, val):
        """
        detects the changes in the sliders and plot these changes using the indx to the band given by th slider
        and the slider value which is the gain
        :param indx: int
        :param val: int
        :return: none
        """
        try:
            self.sliderChangedGraph.plotItem.clear()
            if val < 0 and not 0:
                self.sliderValuesClicked[indx] = 1/val
            else:
                self.sliderValuesClicked[indx] = val
            self.getWindow()
            self.signalModification = applyWindowFunction(indx, self.sliderValuesClicked, self.signalBandsCopy, equalizerApp.windowMode)
            try:
                 self.plotFourier(self.sliderChangedGraph, self.signalModification, self.pens[2])
            except:
                print("failed")
                pass
            self.signalModificationInv = inverseFourierTransform(self.signalModification, self.signalFile['dim'])
        except:
            pass

    def getWindow(self):
        """
        identifies the seleted window
        :return: none
        """
        for window in self.windows:
            if window.isChecked():
                equalizerApp.windowMode = window.text()

    def playResultFile(self):
        """
        play the results from the sliders while checking the dimensions of the file
        :return:
        """
        if len(self.signalFile['dim']) == 2:
            self.dataType = type(self.signalFile['data'][0, 0])
        else:
            self.dataType = type(self.signalFile['data'][0])
        self.fourierArrayModified = np.copy(self.signalFourier['transformedData'])
        self.newInverse = inverseFourierTransform(self.fourierArrayModified, self.signalFile['dim'])
        sd.play(self.newInverse.astype(self.dataType), self.signalFile['frequency'])
        print(self.signalFile['frequency'])

    def plotFourier(self, widgetName, data, pen):
        """
        plot the fourier transform of the data
        :data: the data to be plotted
        :return:
        """
        try:
            N = len(data)
            yplot = 2.0 / N * np.abs(data[: N//2])
            widgetName.plotItem.plot(yplot, pen= pen)
        except:
            pass
    def resetAllBands(self):
        """
        resets al equalizer processes
        :return:
        """
        try:
            for slider in self.sliders:
                slider.setValue(1)
            self.sliderChangedGraph.plotItem.clear()
            self.plotUsingDimension()
            for slider, value in self.sliderValuesClicked.items():
                self.sliderValuesClicked[slider] = ...
            self.signalModification = ...
            self.signalModificationInv = self.signalFile['data']
        except :
            pass


    def showResultOutput(self):
        self.tabWidget.setCurrentIndex(1)

        for btn in self.saveButtons:
            btn.setEnabled(True)
        for widget in self.outputWidgets:
            widget.plotItem.clear()
        # Plot Original signal in inputTimeOriginal Widget
        self.inputTimeOriginal.plotItem.plot(self.signalFile['data'])

        # Plot Inverse of Original in outputTimeOriginal Widget
        self.outputTimeModified.plotItem.plot(self.signalModificationInv)


        # Plot Original Signal in inputFourierOriginal Widget
        self.plotFourier(self.inputFourierOriginal, self.signalFourier['transformedData'], pen=self.pens[2])


        #  Plot Fourier of Original in outputFourierOriginal Widget
        self.plotFourier(self.outputFourierModified, self.signalModification, pen=self.pens[3])

    def compareResults(self):
        print("yes")

        self.tabWidget.setCurrentIndex(-1)
        self.plotFourier(self.result1Plot, self.results[1][0], self.pens[3])
        self.plotFourier(self.result2Plot, self.results[2][0], self.pens[3])

    def saveResult(self):
        if self.resultCounter > 2:
            print("No more yala")
        else:
            self.results[self.resultCounter].append([self.signalModification, self.signalModificationInv])
            self.resultCounter +=1
        print(self.results)
    def saveWaveFile(self, name, rate, data):
        self.showSaveMessage("Save", "Save your file")
        wavfile.write(name, rate, data.astype(self.signalDataType))


    def showDifferenceWindow(self):
        self.popup_window.show()
        self.pop_ui.timeDifference.plotItem.clear()
        self.pop_ui.fourierDifference.plotItem.clear()

        # Difference of signals in Time
        self.signalDiffInTime = self.signalModificationInv - self.signalFile['data']
        self.pop_ui.timeDifference.plotItem.plot(self.signalDiffInTime)

        # Difference of signals in Fourier
        self.signalDiffInFourier = self.signalModification - self.signalFourier['transformedData']
        self.plotFourier(self.pop_ui.fourierDifference, self.signalDiffInFourier, pen=self.pens[3])

    def showSaveMessage(self, message, info):
        msg = QMessageBox()
        msg.setWindowTitle("Save Result")
        msg.setText(message)
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setInformativeText(info)
        x = msg.exec_()


def main():
    """
    the application startup functions
    :return:
    """
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = equalizerApp(MainWindow)
    MainWindow.show()



    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

