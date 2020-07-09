import keyboard
from model import HotkeyModel
import resources_qrc

from PySide2.QtCore import QEvent, QObject, Qt, Signal
from PySide2.QtGui import QColor, QIcon, QKeySequence, QPixmap
from PySide2.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit, 
    QListWidget, 
    QListWidgetItem,
    QMainWindow, 
    QMenu,
    QProxyStyle,
    QPushButton,
    QSizePolicy,
    QStyle,
    QSpacerItem,
    QSystemTrayIcon,     
    QVBoxLayout, 
    QWidget
)

def create_fn_combo():
    # retrieve the labels from winkeyboard. Portability ?
    keys = [keyboard._winkeyboard.official_virtual_keys[i][0] for i in range(0xa6, 0xb8)]
    keys.insert(0, "")
    combo = NoWheelCombobox()
    combo.addItems(keys)
    return combo

class NoWheelCombobox(QComboBox):
    def __init__(self, parent=None):
        super(NoWheelCombobox, self).__init__(parent)

    def wheelEvent(self, event):
        pass

class KeyInputLineEdit(QLineEdit):

    modified = Signal(str, list)
    edition_started = Signal()
    edition_finished = Signal()

    def __init__(self, hotkey_id):
        super(KeyInputLineEdit, self).__init__()
        self.hotkey_id = hotkey_id

    def focusInEvent(self, event):
        super(KeyInputLineEdit, self).focusInEvent(event)      
        self.edition_started.emit()

    def focusOutEvent(self, event):
        super(KeyInputLineEdit, self).focusOutEvent(event)      
        self.edition_finished.emit()

    def contextMenuEvent(self, event):
        pass

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        ignored_keys = [Qt.Key_Meta, Qt.Key_Alt, Qt.Key_AltGr, Qt.Key_Control, Qt.Key_Shift]
        if key in ignored_keys:
            event.ignore()
            return 

        focusout_keys = [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape]
        if mods == Qt.NoModifier and key in focusout_keys:
            self.clearFocus()
            event.ignore()
            return

        key_str = QKeySequence(event.key()).toString()
        mods_str = QKeySequence(event.modifiers()).toString()

        source = [mods_str, key_str]
        key_text = "".join(source)

        if key_text == self.text():
            event.ignore()
            return

        self.setText(key_text)
        self.modified.emit(self.hotkey_id, source)
        event.accept()

class NoFocusStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget):
        if element == QStyle.PE_FrameFocusRect:
            return
        super().drawPrimitive(element, option, painter, widget)

class MainView(QMainWindow):

    windowsStateChanged = Signal(bool)

    def __init__(self, model, ctrl):
        super(MainView, self).__init__()
        self.model = model
        self.ctrl = ctrl

        mainwidget = QWidget(self)
        mainlayout = QVBoxLayout(mainwidget)
        mainlayout.setContentsMargins(4, 4, 4, 4)
        self.setCentralWidget(mainwidget)

        self.listwidget = HotkeyListView(self.model, self.ctrl)
        self.listwidget.setStyle(NoFocusStyle())
        self.listwidget.setSelectionMode(QListWidget.NoSelection)
        self.listwidget.update_ui()

        mainlayout.addWidget(self.listwidget)
        self.setWindowTitle("Hotkeys")
        self.setWindowIcon(QIcon(":/icon.png"))
        self.setMinimumSize(450, 250)

        self.listwidget.create_hotkey_requested.connect(self.create_hotkey_requested)
        self.listwidget.delete_hotkey_requested.connect(self.delete_hotkey_requested)
        self.listwidget.source_hotkey_modified.connect(ctrl.modify_source)
        self.listwidget.target_hotkey_modified.connect(ctrl.modify_target)
        self.listwidget.edition_started.connect(ctrl.unregister_all)
        self.listwidget.edition_finished.connect(ctrl.register_all)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            self.windowsStateChanged.emit(self.windowState()&Qt.WindowMinimized)

    def create_hotkey_requested(self):
        self.ctrl.create()
        self.listwidget.update_ui()

    def delete_hotkey_requested(self, uid):
        self.ctrl.delete(uid)
        self.listwidget.update_ui()

class HotkeyListView(QListWidget):

    create_hotkey_requested = Signal()
    delete_hotkey_requested = Signal(str)
    source_hotkey_modified = Signal(str, list)
    target_hotkey_modified = Signal(str, str)
    edition_started = Signal()
    edition_finished = Signal()

    def __init__(self, model, ctrl):
        super(HotkeyListView, self).__init__()
        self._model = model
        self._ctrl = ctrl
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        menu = QMenu()
        menu.addAction("add", lambda: self.create_hotkey_requested.emit())

        item = self.itemAt(pos)
        if item:
            hotkey_id = item.data(Qt.UserRole)
            menu.addAction("remove", lambda: self.delete_hotkey_requested.emit(hotkey_id))

        menu.exec_(self.mapToGlobal(pos))

    def update_ui(self):
        self.clear()

        for hotkey in self._model._hotkeys:
            hotkey_id = str(hotkey.id)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 4, 4, 4)

            source_le = KeyInputLineEdit(hotkey_id)
            source_le.setText("".join(hotkey.source))
            source_le.modified.connect(self.source_hotkey_modified)
            source_le.edition_started.connect(self.edition_started)
            source_le.edition_finished.connect(self.edition_finished)

            target_cb = create_fn_combo()
            target_cb.setProperty("id", hotkey_id)
            target_cb.setCurrentText(hotkey.target)
            target_cb.currentTextChanged.connect(self.target_edited)
            row_widget.adjustSize()         

            keyboard_pix = QPixmap(":/keyboard.png")
            keyboard_pix = keyboard_pix.scaledToWidth(24, Qt.SmoothTransformation)
            source_holder = QLabel()
            source_holder.setWindowIcon
            source_holder.setPixmap(keyboard_pix)            
            
            target_pix = QPixmap(":/target.png")
            target_pix = target_pix.scaledToWidth(18, Qt.SmoothTransformation)
            target_holder = QLabel()
            target_holder.setPixmap(target_pix)     

            row_layout.addWidget(source_holder)
            row_layout.addWidget(source_le)
            row_layout.addStretch()
            row_layout.addWidget(target_holder)
            row_layout.addWidget(target_cb)

            item = QListWidgetItem(self)
            item.setData(Qt.UserRole, hotkey_id)
            item.setSizeHint(row_widget.sizeHint())
            self.setItemWidget(item, row_widget) 

        
        self._ctrl.error_triggered.connect(self.error_received)
        self._ctrl.error_cleared.connect(self.error_cleared) 

    def target_edited(self, target):
        uid = self.sender().property("id")
        self.target_hotkey_modified.emit(uid, target)
        self.edition_started.emit()
        self.edition_finished.emit()

    def error_received(self, hotkey_id, msg):
        count = self.count()
        for i in range(count):
            item = self.item(i)
            item_id = item.data(Qt.UserRole)
            if item_id == hotkey_id:
                item.setToolTip(msg)
                item.setBackground(QColor(200, 30, 30))
                self.repaint()
                break

    def error_cleared(self):
        count = self.count()
        for i in range(count):
            item = self.item(i)
            item.setBackground(Qt.white)
            item.setToolTip("")

class SystemTrayIcon(QSystemTrayIcon, QObject):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        menu = QMenu(parent)
        self.exit_action = menu.addAction("Exit")
        self.exit_action.triggered.connect(qApp.quit)
        self.setContextMenu(menu)