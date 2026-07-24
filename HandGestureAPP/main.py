import sys
import mediapipe as mp  # Workaround para conflito de DLL com PyQt5 no Windows
from PyQt5.QtWidgets import QApplication
from views.main_window import HandsGestureRPS

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HandsGestureRPS()
    window.show()
    sys.exit(app.exec_())
