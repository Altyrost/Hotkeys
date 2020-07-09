import keyboard
import signal
import sys
import json

from model import *
from ui import *
from ctrl import *
import resources_qrc

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)

        try:
            verbose_arg = str(sys.argv[1])
            self.verbose = verbose_arg == "-v" or verbose_arg == "--verbose"
        except ValueError:
            self.verbose = False
        except IndexError:
            self.verbose = False

        self.setWindowIcon(QIcon(":/icon.png"))

        self.model = HotkeyListModel()
        self.ctrl = HotkeyController(self.model)

        self.ui = MainView(self.model, self.ctrl)
        self.systray = SystemTrayIcon(QIcon(":/systray_icon.png"))

        self.ui.windowsStateChanged.connect(self.MainwindowStateChanged)
        self.systray.activated.connect(self.systray_activated) 
        self.systray.exit_action.triggered.connect(self.quit)

        self.aboutToQuit.connect(self.model.save)

    def exec_(self):
        self.ctrl.register_all()
        self.ui.show()  
        return super().exec_()

    def MainwindowStateChanged(self, is_minimized):
        if is_minimized:
            self.ui.hide()
            self.systray.show()        

    def systray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.ui.show()  
            self.ui.setWindowState(self.ui.windowState()&Qt.WindowActive)
            self.systray.hide()  

def main():   
    app = App(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL) #fix ctrl+c on windows
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 