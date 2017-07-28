import sys
from classes.sparser import SParser
from PyQt5.QtWidgets import QLabel, QMainWindow, QWidget, QMessageBox, QApplication, QPushButton, QFileDialog, QLineEdit, QTextEdit, QGridLayout
from PyQt5.QtCore import QCoreApplication


class Example(QMainWindow):

    nnfilelabel = None
    pythonfilelabel = None
    nnstatuslabel = None
    sexpr = None
    inputfield = None
    layersfield = None
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):

        w = QWidget(self)

        nnlabel = QLabel("NN file")
        self.nnfilelabel = QLineEdit()
        self.nnfilelabel.setReadOnly(True)

        pylabel = QLabel("Target Python file")
        self.pythonfilelabel = QLineEdit()
        self.pythonfilelabel.setReadOnly(True)

        self.nnstatuslabel=QLabel()
        self.nnstatuslabel.setText("Please select an NN file for parsing.")

        inputlabel = QLabel("Input format: ")
        self.inputfield = QLineEdit()
        self.inputfield.setReadOnly(True)

        layerslabel = QLabel("Network layers: ")
        self.layersfield = QTextEdit()
        self.layersfield.setReadOnly(True)
        

        qbtn = QPushButton('Browse', self)
        qbtn.clicked.connect(self.openFileDialog)
        #qbtn.resize(qbtn.sizeHint())

        qbtn2 = QPushButton('Browse', self)
        qbtn2.clicked.connect(self.saveFileDialog)
        #qbtn2.resize(qbtn.sizeHint())

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(nnlabel, 1, 0)
        grid.addWidget(self.nnfilelabel, 1, 1)
        grid.addWidget(qbtn, 1, 2)

        grid.addWidget(self.nnstatuslabel, 2, 1)

        grid.addWidget(inputlabel, 3, 0)
        grid.addWidget(self.inputfield, 3, 1)

        grid.addWidget(layerslabel, 4, 0)
        grid.addWidget(self.layersfield, 4, 1)


        grid.addWidget(pylabel, 5, 0)
        grid.addWidget(self.pythonfilelabel, 5, 1)
        grid.addWidget(qbtn2, 5, 2)


        w.setLayout(grid)

        self.setCentralWidget(w)
            
        self.setGeometry(300, 300, 500, 200)        
        self.setWindowTitle('KeraGen v0.1.0a')   
        
        self.statusBar().showMessage('Ready')    
        self.show()
    
    def openFileDialog(self):    
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"NN File selection", "","All Files (*);;Neural Net files (*.nn)", "Neural Net files (*.nn)", options=options)
        if fileName:
            self.nnfilelabel.setText(fileName)
            self.parseAndValidateNNFile(fileName)
            
    def parseAndValidateNNFile(self, fileName):
        self.nnstatuslabel.setText("Parsing...")
        try:
            self.sexpr = SParser(fileName).parse(False)
            self.nnstatuslabel.setText("Validating...")
            self.sexpr.validate(True)
            self.nnstatuslabel.setText("Valid!")
            self.displayLayers()
        except (RuntimeError, RuntimeWarning) as e:
            self.nnstatuslabel.setText("Error in NN file: {0}".format(e))
            self.sexprfield.setText("Parsed NN file is invalid.")
        
    def displayLayers(self):
        self.inputfield.setText(str(self.sexpr.search_children_of("input")))
        for layer in self.sexpr.search_all(["fc", "conv2d", "pool"]):
            self.layersfield.setText(self.layersfield.toPlainText()
            + str(layer.root)+" -> Output: "+layer.search_children_of("output")+ ", SIMD: " +layer.search_children_of("simd")+"\n")

    def saveFileDialog(self):    
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Target Python file selection","","All Files (*);;Python files (*.py)", "Python files (*.py)", options=options)
        if fileName:
            self.pythonfilelabel.setText(fileName)

    def closeEvent(self, event):
        
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()        
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())