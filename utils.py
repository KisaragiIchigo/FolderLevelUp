# utils.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle


# パス系（Windows onefile対応）

TOOL_NAME = "FolderLevelUp"  

def is_windows() -> bool:
    return os.name == "nt"

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)

def app_base_dir() -> str:

    if is_windows() and is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def config_dir() -> str:
    return os.path.join(app_base_dir(), "config")

def logs_dir() -> str:
    return os.path.join(app_base_dir(), "logs")

def config_path() -> str:
    return os.path.join(config_dir(), f"[config]{TOOL_NAME}_config.json")

def log_path() -> str:
    return os.path.join(logs_dir(), f"[config]{TOOL_NAME}app.log")

def ensure_dirs() -> None:
    try:
        os.makedirs(config_dir(), exist_ok=True)
        os.makedirs(logs_dir(), exist_ok=True)
    except Exception as e:
        print(f"ディレクトリ作成エラー: {e}")


# ロギング初期化（Rotating）

_LOGGER_INITIALIZED = False

def setup_logging(level: int = logging.INFO) -> None:
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return
    ensure_dirs()
    lp = log_path()

    logger = logging.getLogger()
    logger.setLevel(level)

    handler_exists = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    if not handler_exists:
        handler = RotatingFileHandler(lp, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)


    logging.info("=== Logging start ===")
    logging.info(f"BaseDir        : {app_base_dir()}")
    logging.info(f"Config Path    : {config_path()}")
    logging.info(f"Log Path       : {lp}")
    _LOGGER_INITIALIZED = True



def resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    p = os.path.join(base, rel_path)
    return p if os.path.exists(p) else rel_path

def set_app_icon_if_exists(widget):
    ico = resource_path("FolderLevelUp.ico")
    if os.path.exists(ico):
        widget.setWindowIcon(QIcon(ico))
    else:
        widget.setWindowIcon(widget.style().standardIcon(QStyle.SP_ComputerIcon))

# --- ウィンドウ位置/サイズ 保存・復元 ---
def save_window_state(widget, cfg):
    g = widget.geometry()
    cfg.window = {"x": g.x(), "y": g.y(), "w": g.width(), "h": g.height()}

def load_window_state(widget, cfg):
    w = getattr(cfg, "window", None)
    if not w:
        return
    try:
        widget.setGeometry(w["x"], w["y"], w["w"], w["h"])
    except Exception:
        pass


# QSS（GUIsample記法準拠・高視認UI）

def app_qss() -> str:
    PRIMARY_COLOR    = "#4169e1"
    HOVER_COLOR      = "#7000e0"
    TITLE_COLOR      = "#FFFFFF"
    TEXT_COLOR       = "#FFFFFF"
    CLOSEBTN_COLOR   = "#FF0000"
    MINBTN_COLOR     = "#FFD600"
    MAXBTN_COLOR     = "#00C853"

    WINDOW_BG        = "rgba(255,255,255,0)"
    GLASSROOT_BG     = "rgba(5,5,51,230)"
    GLASSROOT_BORDER = "3px solid rgba(65,105,255,255)"
    TEXTPANEL_BG     = "#579cdd"
    BORDER_DROP_DASHED = f"2px dashed {PRIMARY_COLOR}"

    RADIUS_WINDOW    = 18
    RADIUS_CARD      = 16
    RADIUS_PANEL     = 10
    RADIUS_BUTTON    = 8
    RADIUS_CLOSE     = 6
    RADIUS_DROP      = 12

    DD_HOVER_BG      = "rgba(65,105,225,48)"
    DD_HOVER_FG      = "#0b2a6a"

    glass_grad = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 rgba(255,255,255,50), stop:0.5 rgba(200,220,255,25), stop:1 rgba(255,255,255,8))"
    )
    menu_grad  = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,12), stop:1 rgba(255,255,255,6))"
    )

    return f"""
    QWidget#bgRoot {{
        background-color: {WINDOW_BG};
        border-radius: {RADIUS_WINDOW}px;
    }}
    QWidget#glassRoot {{
        background-color: {GLASSROOT_BG};
        border: {GLASSROOT_BORDER};
        border-radius: {RADIUS_CARD}px;
        background-image: {glass_grad};
        background-repeat: no-repeat;
        background-position: 0 0;
    }}

    QLabel#titleLabel {{
        color: {TITLE_COLOR};
        font-weight: bold;
        font-size: 10pt;
    }}
    .HeadingLabel {{ color:#b8dcff; font-weight:bold; }}

    QLabel#dropArea {{
        border: {BORDER_DROP_DASHED};
        border-radius: {RADIUS_DROP}px;
        background-color: rgba(25, 25, 112, 0.5);
        color: #177ee6;
        font-weight: bold;
    }}

    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        padding: 6px 10px;
        border-radius: {RADIUS_BUTTON}px;
    }}
    QPushButton:hover {{ background-color: {HOVER_COLOR}; }}

    QPushButton#minBtn {{ background:transparent; color:{MINBTN_COLOR}; border-radius:{RADIUS_CLOSE}px; font-weight:bold; padding:0px; }}
    QPushButton#minBtn:hover {{ background: rgba(153,179,255,0.06); }}
    QPushButton#maxBtn {{ background:transparent; color:{MAXBTN_COLOR}; border-radius:{RADIUS_CLOSE}px; font-weight:bold; padding:0px; }}
    QPushButton#maxBtn:hover {{ background: rgba(153,179,255,0.06); }}
    QPushButton#closeBtn {{ background:transparent; color:{CLOSEBTN_COLOR}; border-radius:{RADIUS_CLOSE}px; font-weight:bold; padding:0px; }}
    QPushButton#closeBtn:hover {{ background: rgba(153,179,255,0.06); }}

    QProgressBar {{
        border: 1px solid #555; border-radius: 5px; text-align: center; background-color: #333; color: white;
    }}
    QProgressBar::chunk {{ background-color: {PRIMARY_COLOR}; border-radius: 5px; }}

    .DarkPanel, #textPanel {{
        background-color: {TEXTPANEL_BG};
        border-radius: {RADIUS_PANEL}px;
        border: 1px solid rgba(0,0,0,120);
        padding: 8px;
    }}
    .DarkPanel QLabel, .DarkPanel QLineEdit, .DarkPanel QComboBox, .DarkPanel QDateEdit,
    .DarkPanel QCheckBox, .DarkPanel QRadioButton, .DarkPanel QSpinBox,
    #textPanel QTextEdit, #textPanel QListWidget {{
        color: {TEXT_COLOR};
        background-color: transparent;
    }}

    .DarkPanel QLineEdit, .DarkPanel QComboBox, .DarkPanel QDateEdit {{
        background-color: #ffe4e1; border-radius: 3px; color: #000; border: 1px solid #888; padding: 2px;
    }}

    .DarkPanel QComboBox QAbstractItemView::item:hover {{ background: {DD_HOVER_BG}; color: {DD_HOVER_FG}; }}
    .DarkPanel QComboBox QAbstractItemView {{
        background-color: #ffe4e1; color: #191970; border: 1px solid #888;
        selection-background-color: {PRIMARY_COLOR}; outline: none;
    }}

    QTreeWidget::item:selected, QListWidget::item:selected {{
        background-color: rgba(65,105,225, 210);
        color: white;
    }}
    QTreeWidget::item:hover, QListWidget::item:hover {{
        background-color: rgba(65,105,225, 110);
    }}

    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background: rgba(87,156,221,100);
        color: #3a7aba;
        padding: 6px 10px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{ background: {TEXTPANEL_BG}; color: white; }}

    QCheckBox::indicator, QRadioButton::indicator {{ width:14px; height:14px; border:1px solid #888; background-color:#ffe4e1; }}
    QRadioButton::indicator {{ border-radius:7px; }}
    QCheckBox::indicator {{ border-radius:3px; }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border:1px solid {PRIMARY_COLOR}; }}
    QCheckBox::indicator:checked {{ background-color:{PRIMARY_COLOR}; border:1px solid {PRIMARY_COLOR}; }}
    QRadioButton::indicator:checked {{
        border:1px solid {PRIMARY_COLOR};
        background-color:qradialgradient(cx:0.5,cy:0.5,radius:0.4,fx:0.5,fy:0.5,stop:0 white,stop:1 {PRIMARY_COLOR});
    }}

    QCalendarWidget {{ background:#2f2f2f; color:#000; border:1px solid #666; selection-background-color:{PRIMARY_COLOR}; }}
    QCalendarWidget QToolButton {{ color:#eaeaea; }}

    QWidget#menuPanel {{
        background: {GLASSROOT_BG};
        border: {GLASSROOT_BORDER};
        border-top-right-radius: {RADIUS_CARD}px; border-bottom-right-radius: {RADIUS_CARD}px;
        background-image: {menu_grad};
        background-repeat: no-repeat; background-position: 0 0;
    }}
    QWidget#overlay {{ background: rgba(0,0,0,120); }}
    QPushButton.menuItem {{ text-align: left; padding: 8px 10px; }}
    QLabel#menuCaption {{ font-size: 7pt; }}
    QPushButton#menuBackBtn {{ background: transparent; color: #222; padding: 2px 6px; border-radius: 6px; }}
    QPushButton#menuBackBtn:hover {{ background: rgba(0,0,0,0.06); }}
    """

# ===== Explorer（Windows）へ変更通知 =====
def _is_windows() -> bool:
    return os.name == "nt"

def shell_notify_update(path: str, is_dir: bool | None = None):
    if not _is_windows(): return
    try:
        import ctypes
        if is_dir is None:
            is_dir = os.path.isdir(path)
        SHCNE_UPDATEDIR   = 0x00001000
        SHCNE_UPDATEITEM  = 0x00002000
        SHCNF_PATHW       = 0x0005
        event = SHCNE_UPDATEDIR if is_dir else SHCNE_UPDATEITEM
        ctypes.windll.shell32.SHChangeNotify(event, SHCNF_PATHW, ctypes.c_wchar_p(path), None)
    except Exception:
        pass

def shell_notify_rename(old_path: str, new_path: str, is_folder: bool = True):
    if not _is_windows(): return
    try:
        import ctypes
        SHCNE_RENAMEITEM   = 0x00000001
        SHCNE_RENAMEFOLDER = 0x00020000
        SHCNF_PATHW        = 0x0005
        event = SHCNE_RENAMEFOLDER if is_folder else SHCNE_RENAMEITEM
        ctypes.windll.shell32.SHChangeNotify(
            event, SHCNF_PATHW, ctypes.c_wchar_p(old_path), ctypes.c_wchar_p(new_path)
        )
        SHCNE_ALLEVENTS = 0x7FFFFFFF
        SHCNF_FLUSH     = 0x1000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ALLEVENTS, SHCNF_FLUSH, None, None)
    except Exception:
        pass
