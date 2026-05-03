import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import Qt
from rocky_window    import RockyWindow
from chat_window     import ChatWindow


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setQuitOnLastWindowClosed(False)   # keep alive when chat closes

    rocky = RockyWindow()
    chat  = ChatWindow(rocky)

    rocky.open_chat.connect(chat.toggle_visible)
    rocky.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
