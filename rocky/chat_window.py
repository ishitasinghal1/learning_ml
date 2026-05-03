import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QLabel, QLineEdit,
                              QPushButton, QFrame)
from PyQt5.QtCore    import Qt, QTimer, pyqtSignal
from PyQt5.QtGui     import QFont

DARK_BG  = "#0d0d1a"
MID_BG   = "#13132b"
ACCENT   = "#20D3A5"
TEXT     = "#e0e0e0"
USER_BG  = "#1a3a5c"
ROCKY_BG = "#1e1e2e"
SUBTLE   = "#555577"

CHAT_W = 340
CHAT_H = 500


class MsgBubble(QFrame):
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setMaximumWidth(260)
        if is_user:
            lbl.setStyleSheet(f"background:{USER_BG};color:{TEXT};border-radius:14px;border-bottom-right-radius:3px;padding:8px 12px;")
        else:
            lbl.setStyleSheet(f"background:{ROCKY_BG};color:{ACCENT};border-radius:14px;border-bottom-left-radius:3px;padding:8px 12px;")
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 2, 6, 2)
        if is_user:
            row.addStretch(); row.addWidget(lbl)
        else:
            dot = QLabel("👽"); dot.setFixedSize(22, 22)
            row.addWidget(dot); row.addWidget(lbl); row.addStretch()
        self.setStyleSheet("background:transparent;")


class ChatWindow(QWidget):
    _response_ready = pyqtSignal(str)

    def __init__(self, rocky):
        super().__init__()
        self.rocky = rocky
        self._busy = False
        self._response_ready.connect(self._on_response)
        self._build_ui()

    def _build_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setFixedSize(CHAT_W, CHAT_H)
        self.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background:{MID_BG};border-top-left-radius:18px;border-top-right-radius:18px;")
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(14, 0, 10, 0)
        title = QLabel("👽  Rocky")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet(f"color:{ACCENT};background:transparent;")
        sub = QLabel("your alien companion")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet(f"color:{SUBTLE};background:transparent;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"QPushButton{{background:transparent;color:{SUBTLE};border:none;font-size:14px;font-weight:bold;}}QPushButton:hover{{color:#ff5555;}}")
        close_btn.clicked.connect(self.hide)
        titles = QVBoxLayout(); titles.setSpacing(0)
        titles.addWidget(title); titles.addWidget(sub)
        h_row.addLayout(titles); h_row.addStretch(); h_row.addWidget(close_btn)
        root.addWidget(header)

        # Messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background:{DARK_BG};border:none;")
        self.scroll.verticalScrollBar().setStyleSheet("QScrollBar:vertical{width:4px;background:transparent;}QScrollBar::handle:vertical{background:#333355;border-radius:2px;}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        self._msg_box = QWidget()
        self._msg_box.setStyleSheet(f"background:{DARK_BG};")
        self._msg_layout = QVBoxLayout(self._msg_box)
        self._msg_layout.setAlignment(Qt.AlignTop)
        self._msg_layout.setSpacing(6)
        self._msg_layout.setContentsMargins(6, 10, 6, 10)
        self.scroll.setWidget(self._msg_box)
        root.addWidget(self.scroll)

        # Thinking
        self._thinking_lbl = QLabel("  Rocky is thinking…")
        self._thinking_lbl.setFont(QFont("Segoe UI", 9))
        self._thinking_lbl.setStyleSheet(f"color:{SUBTLE};background:{DARK_BG};padding:3px 10px;")
        self._thinking_lbl.hide()
        root.addWidget(self._thinking_lbl)

        # Input
        inp_frame = QFrame()
        inp_frame.setFixedHeight(56)
        inp_frame.setStyleSheet(f"background:{MID_BG};border-bottom-left-radius:18px;border-bottom-right-radius:18px;")
        inp_row = QHBoxLayout(inp_frame)
        inp_row.setContentsMargins(12, 10, 12, 10); inp_row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Talk to Rocky…")
        self.input.setFont(QFont("Segoe UI", 10))
        self.input.setStyleSheet(f"QLineEdit{{background:#08081a;color:{TEXT};border:1px solid #2a2a4a;border-radius:10px;padding:5px 12px;}}QLineEdit:focus{{border-color:{ACCENT};}}")
        self.input.returnPressed.connect(self._send)
        self._send_btn = QPushButton("↑")
        self._send_btn.setFixedSize(36, 36)
        self._send_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._send_btn.setStyleSheet(f"QPushButton{{background:{ACCENT};color:#0a0a1a;border:none;border-radius:10px;}}QPushButton:hover{{background:#2effc8;}}QPushButton:disabled{{background:#1a5544;color:#336655;}}")
        self._send_btn.clicked.connect(self._send)
        inp_row.addWidget(self.input); inp_row.addWidget(self._send_btn)
        root.addWidget(inp_frame)

        self._add_msg("Rocky is here. Question.", is_user=False)

    def closeEvent(self, event):
        event.ignore(); self.hide()

    def toggle_visible(self):
        if self.isVisible():
            self.hide(); return

        from PyQt5.QtWidgets import QApplication
        sr = QApplication.primaryScreen().availableGeometry()
        rp = self.rocky.pos()   # Rocky window top-left
        rw = self.rocky.width()

        # Chat sits directly ABOVE Rocky, right-edge flush with Rocky's right edge
        x = rp.x() + rw - CHAT_W
        y = rp.y() - CHAT_H        # bottom of chat touches top of Rocky

        # Clamp to screen bounds
        x = max(sr.x(), min(x, sr.x() + sr.width() - CHAT_W))
        y = max(sr.y(), y)

        self.move(x, y); self.show(); self.raise_()
        self.activateWindow(); self.input.setFocus()

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.input.setEnabled(not busy)
        self._send_btn.setEnabled(not busy)
        self._thinking_lbl.setVisible(busy)

    def _send(self):
        if self._busy: return
        text = self.input.text().strip()
        if not text: return
        self.input.clear()
        self._add_msg(text, is_user=True)
        self._set_busy(True)
        self.rocky.set_anim("thinking")
        threading.Thread(target=self._fetch, args=(text,), daemon=True).start()

    def _fetch(self, text: str):
        try:
            from agent import get_response
            reply = get_response(text)
        except Exception as e:
            reply = f"Rocky confused. Error: {type(e).__name__}: {e}"
        try:
            self._response_ready.emit(reply)
        except RuntimeError:
            pass

    def _on_response(self, text: str):
        self._set_busy(False)
        self._add_msg(text, is_user=False)
        preview = text[:70] + ("…" if len(text) > 70 else "")
        self.rocky.speak(preview, "talk", duration_ms=5_000)

    def _add_msg(self, text: str, is_user: bool):
        self._msg_layout.addWidget(MsgBubble(text, is_user))
        QTimer.singleShot(60, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))