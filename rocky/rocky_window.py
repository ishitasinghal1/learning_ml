import os, random
from PyQt5.QtWidgets import QWidget, QLabel, QApplication
from PyQt5.QtCore    import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui     import QMovie, QPainter, QPainterPath, QColor, QFont

QUOTES = [
    "Rocky hate Mark.",
    "We are friend. Question.",
    "Rocky is... curious.",
    "Your code is brave.",
    "Rocky senses overthinking. Rocky is correct.",
    "Space is vast. Your bugs are small.",
    "Rocky miss Erid.",
    "You smart. Rocky is smarter.",
    "Problem. Solution. Question.",
    "Rocky observes: coffee again.",
    "Ishita works hard. Rocky approves. Barely.",
    "Astrophage is alive. Question.",
    "I help you. You help me.",
]

REMINDERS = [
    "Does Earth not have water to drink. Question?",
    "Take break. Rocky insists.",
    "Blink. Your eyes are real.",
    "Commit code. Now.",
    "Stand up. Stretch. Rocky commands.",
    "Ate food? Rocky is concerned. Question.",
    "Deadline near? Rocky is also stressed.",
    "Humans sleep at night, you not human. Question?",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ANIMS = {
    "idle1":             os.path.join(BASE_DIR, "pet/animations/idle1.gif"),
    "idle2":             os.path.join(BASE_DIR, "pet/animations/idle2.gif"),
    "talk":              os.path.join(BASE_DIR, "pet/animations/talk.gif"),
    "thinking":          os.path.join(BASE_DIR, "pet/animations/thinking.gif"),
    "happy":             os.path.join(BASE_DIR, "pet/animations/happy.gif"),
    "angry":             os.path.join(BASE_DIR, "pet/animations/angry.gif"),
    "sad":               os.path.join(BASE_DIR, "pet/animations/sad.gif"),
    "surprised":         os.path.join(BASE_DIR, "pet/animations/surprised.gif"),
    "dance":             os.path.join(BASE_DIR, "pet/animations/dance.gif"),
    "dance_celebration": os.path.join(BASE_DIR, "pet/animations/dance_celebration.gif"),
}

ROCKY_PX = 150   # sprite size
WIN_W    = 160   # window = just big enough for the sprite
WIN_H    = 160

IDLE_SWAP_MS = 12_000
QUOTE_MIN_MS =  2 * 60_000
QUOTE_MAX_MS =  5 * 60_000
WATER_MS     = 40 * 60_000
MOOD_MIN_MS  =  6 * 60_000
MOOD_MAX_MS  = 12 * 60_000


# ── Speech Bubble — its own top-level window ─────────────────────────────────
class _Bubble(QWidget):
    BW = 240   # bubble width

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(self.BW)
        self._text = ""
        self._hide_t = QTimer(self, singleShot=True)
        self._hide_t.timeout.connect(self.hide)
        self.hide()

    def speak(self, text: str, rocky_pos: QPoint, ms: int = 5_000):
        self._text = text
        chars_per_line = (self.BW - 24) // 7
        lines = max(1, -(-len(text) // chars_per_line))
        h = lines * 22 + 36
        self.setFixedHeight(h)

        # Position: to the LEFT of Rocky, vertically centered on Rocky sprite
        x = rocky_pos.x() - self.BW - 6
        y = rocky_pos.y() + (WIN_H - h) // 2
        sr = QApplication.primaryScreen().availableGeometry()
        x = max(sr.x(), x)
        self.move(x, y)

        self.update(); self.show(); self.raise_()
        self._hide_t.start(ms)

    def paintEvent(self, _):
        if not self._text: return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H   = self.width(), self.height()
        body_h = H - 10
        path   = QPainterPath()
        path.addRoundedRect(2, 2, W - 4, body_h - 2, 12, 12)
        # tail points RIGHT toward Rocky
        mid = body_h // 2
        path.moveTo(W - 2, mid - 7)
        path.lineTo(W + 8, mid)
        path.lineTo(W - 2, mid + 7)
        p.fillPath(path, QColor(255, 255, 255, 240))
        p.setPen(QColor(160, 160, 160, 180)); p.drawPath(path)
        p.setPen(QColor(20, 20, 20))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(10, 8, W - 20, body_h - 12, Qt.TextWordWrap, self._text)


# ── Rocky pet window — compact, just the sprite ───────────────────────────────
class RockyWindow(QWidget):
    open_chat = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._drag_start  = QPoint()
        self._drag_origin = QPoint()
        self._did_drag    = False
        self._is_double   = False
        self._cur_anim    = "idle1"
        self._locked      = False
        self._movie       = None
        self.bubble       = _Bubble()   # separate window, not a child
        self._setup_window()
        self._setup_widgets()
        self._setup_timers()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)
        sr = QApplication.primaryScreen().availableGeometry()
        # Bottom-right corner
        self.move(sr.width() - WIN_W - 20, sr.height() - WIN_H - 40)

    def _setup_widgets(self):
        self.lbl = QLabel(self)
        self.lbl.setGeometry(0, 0, WIN_W, WIN_H)
        self.lbl.setCursor(Qt.PointingHandCursor)
        self.lbl.setScaledContents(True)
        self.set_anim("idle1")

    def _setup_timers(self):
        self._idle_t = QTimer(self)
        self._idle_t.timeout.connect(self._swap_idle)
        self._idle_t.start(IDLE_SWAP_MS)

        self._quote_t = QTimer(self, singleShot=True)
        self._quote_t.timeout.connect(self._fire_quote)
        self._quote_t.start(random.randint(QUOTE_MIN_MS, QUOTE_MAX_MS))

        self._water_t = QTimer(self)
        self._water_t.timeout.connect(self._fire_water)
        self._water_t.start(WATER_MS)

        self._mood_t = QTimer(self, singleShot=True)
        self._mood_t.timeout.connect(self._fire_mood)
        self._mood_t.start(random.randint(MOOD_MIN_MS, MOOD_MAX_MS))

    # ── Public ────────────────────────────────────────────────────────────────
    def set_anim(self, name: str):
        path = ANIMS.get(name, ANIMS["idle1"])
        if not os.path.exists(path): return
        if self._movie: self._movie.stop()
        m = QMovie(path)
        m.setScaledSize(self.lbl.size())
        self.lbl.setMovie(m); m.start()
        self._movie = m; self._cur_anim = name

    def speak(self, text: str, emotion: str = "talk", duration_ms: int = 5_000):
        self._locked = True
        self.set_anim(emotion)
        self.bubble.speak(text, self.pos(), ms=duration_ms)
        QTimer.singleShot(duration_ms + 300, self._return_idle)

    def _return_idle(self):
        self._locked = False
        self.set_anim("idle1")

    # ── Timers ────────────────────────────────────────────────────────────────
    def _swap_idle(self):
        if not self._locked and self._cur_anim in ("idle1", "idle2"):
            self.set_anim("idle2" if self._cur_anim == "idle1" else "idle1")

    def _fire_quote(self):
        if not self._locked:
            self.speak(random.choice(QUOTES + REMINDERS), "talk", 5_000)
        self._quote_t.start(random.randint(QUOTE_MIN_MS, QUOTE_MAX_MS))

    def _fire_water(self):
        if not self._locked:
            self.speak("Drank water? Question.", "thinking", 6_000)

    def _fire_mood(self):
        if not self._locked:
            emotion, text, dur = random.choice([
                ("happy",            "Rocky is happy today. Question.",         3_500),
                ("surprised",        "Oh. Interesting. Question.",              3_500),
                ("angry",            "Rocky is annoyed. Something is wrong.",   3_500),
                ("sad",              "Rocky misses Erid. Question.",            3_500),
                ("dance",            "Rocky feels music. Question.",            10_000),
                ("dance_celebration","Ishita is doing well! Rocky celebrates.", 10_000),
            ])
            self._locked = True
            self.set_anim(emotion)
            self.bubble.speak(text, self.pos(), ms=dur)
            QTimer.singleShot(dur + 300, self._return_idle)
        self._mood_t.start(random.randint(MOOD_MIN_MS, MOOD_MAX_MS))

    # ── Mouse ─────────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start  = e.globalPos()
            self._drag_origin = self.pos()
            self._did_drag    = False
            self._is_double   = False

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            if (e.globalPos() - self._drag_start).manhattanLength() > 6:
                self._did_drag = True
                self.move(self._drag_origin + (e.globalPos() - self._drag_start))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and not self._did_drag:
            self._click_t = QTimer(self, singleShot=True)
            self._click_t.timeout.connect(self._do_single_click)
            self._click_t.start(250)

    def _do_single_click(self):
        if not self._is_double:
            self.open_chat.emit()
            self.set_anim("happy")
            QTimer.singleShot(2_000, lambda: self.set_anim("idle1"))

    def mouseDoubleClickEvent(self, e):
        self._is_double = True
        if hasattr(self, "_click_t"):
            self._click_t.stop()
        self._locked = True
        self.set_anim(random.choice(["dance", "dance_celebration"]))
        QTimer.singleShot(10_000, self._return_idle)