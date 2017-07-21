import sys
from PyQt5.QtWidgets import QApplication, QWidget

if __name__ == '__main__':
    
    app = QApplication(sys.argv)

    w = QWidget()
    w.resize(1000, 600)
    w.move(300, 300)
    w.setWindowTitle('KeraGen v0.1.0 Alpha 0')
    w.show()
    
    sys.exit(app.exec_())