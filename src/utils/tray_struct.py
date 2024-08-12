import ctypes
import uuid
from ctypes import wintypes
import win32gui
import time


# Define the TBBUTTON structure
class TBBUTTON(ctypes.Structure):
    _fields_ = [
        ("iBitmap", ctypes.c_int),
        ("idCommand", ctypes.c_int),
        ("fsState", ctypes.c_byte),
        ("fsStyle", ctypes.c_byte),
        ("bReserved", ctypes.c_ubyte * 6),
        ("dwData", ctypes.c_ulong),
        ("iString", ctypes.c_int),
    ]


# Define the GUID structure (equivalent of C# Guid type)
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


# Define the TrayItem structure
class TrayItem(ctypes.Structure):
    _fields_ = [
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("dwState", wintypes.DWORD),
        ("uVersion", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("uIconDemoteTimerID", wintypes.WPARAM),
        ("dwUserPref", wintypes.DWORD),
        ("dwLastSoundTime", wintypes.DWORD),
        ("szExeName", wintypes.WCHAR * 260),
        ("szIconText", wintypes.WCHAR * 260),
        ("uNumSeconds", wintypes.UINT),
        ("guidItem", GUID),
    ]

    @property
    def guidItem_python(self):
        return uuid.UUID(bytes_le=bytes(self.guidItem))

    @guidItem_python.setter
    def guidItem_python(self, guid):
        if isinstance(guid, uuid.UUID):
            self.guidItem = GUID(*guid.fields)
        else:
            raise ValueError("Must be a UUID object")


class NotifyIcon:
    def __init__(self, hwnd, uid, icon, title, version, callback_message):
        self.hwnd = hwnd
        self.uid = uid
        self.icon = icon
        self.title = title
        self.version = int(version)
        self.callback_message = callback_message

        # Initialize the timers
        self._last_l_click = self.Stopwatch()
        self._last_r_click = self.Stopwatch()

    class Stopwatch:
        # Replicates the StopWatch class from C#
        def __init__(self):
            self.start_time = time.time()

        def start(self):
            self.start_time = time.time()

        def elapsed_milliseconds(self):
            return int((time.time() - self.start_time) * 1000)

    # FIX: Give a better name to the handle classes
    def handle_left_click(self):
        # returns the elapsed time since last left click
        elapsed = self._last_l_click.elapsed_milliseconds()
        self._last_l_click.start()
        return elapsed

    def handle_right_click(self):
        # returns the elapsed time since last right click
        elapsed = self._last_r_click.elapsed_milliseconds()
        self._last_r_click.start()
        return elapsed

    def send_message(self, message, mouse):
        return win32gui.SendMessage(
            self.hwnd,
            self.callback_message,
            self.get_message_wparam(mouse),
            message | (self.get_message_hiword() << 16),
        )

    def get_message_hiword(self):
        if self.version > 3:
            return self.uid
        return 0

    def get_message_wparam(self, mouse):
        if self.version > 3:
            return mouse
        return self.uid
