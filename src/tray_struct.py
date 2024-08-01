import ctypes
import uuid
from ctypes import wintypes


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
