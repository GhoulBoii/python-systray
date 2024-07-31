import commctrl, win32con
import win32api
import win32gui
import win32ui
import win32process
import ctypes
import struct
from PIL import Image, ImageDraw
from ctypes import wintypes
import uuid

# Add these constants
WM_GETICON = 0x007F
ICON_SMALL = 0
ICON_BIG = 1
TB_GETBUTTON = 0x417
TBSTATE_HIDDEN = 0x8

# represent the TBBUTTON structure
class TBBUTTON(ctypes.Structure):
    _fields_ = [
        ('iBitmap', ctypes.c_int),
        ('idCommand', ctypes.c_int),
        ('fsState', ctypes.c_byte),
        ('fsStyle', ctypes.c_byte),
        ('bReserved', ctypes.c_ubyte * 6),
        ('dwData', ctypes.c_ulong),
        ('iString', ctypes.c_int),
    ]

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

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
        ("guidItem", GUID)
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

def get_tray_item(i, h_buffer, h_process, toolbar_hwnd):
    tb_button = TBBUTTON()
    tray_item = TrayItem()

    # Send message to get button information
    win32gui.SendMessage(toolbar_hwnd, TB_GETBUTTON, i, h_buffer)

    # Read the memory into our button struct
    button_info_buffer = win32process.ReadProcessMemory(h_process, h_buffer, ctypes.sizeof(TBBUTTON))
    ctypes.memmove(ctypes.addressof(tb_button), button_info_buffer, ctypes.sizeof(TBBUTTON))

    if tb_button.dwData != 0:
        # Read the TrayItem data
        tray_item_buffer = win32process.ReadProcessMemory(h_process, tb_button.dwData, ctypes.sizeof(TrayItem))
        ctypes.memmove(ctypes.addressof(tray_item), tray_item_buffer, ctypes.sizeof(TrayItem))

        # Set the state
        if tb_button.fsState & TBSTATE_HIDDEN:
            tray_item.dwState = 1
        else:
            tray_item.dwState = 0

        print(f"ExplorerTrayService: Got tray item: {tray_item.szIconText}")

    return tray_item

# Usage example (you'll need to set these values appropriately)
hWnd = win32gui.FindWindow("Shell_TrayWnd", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "TrayNotifyWnd", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "SysPager", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "ToolbarWindow32", None)

# get the count of icons in the tray
numIcons = win32api.SendMessage(hWnd, commctrl.TB_BUTTONCOUNT, 0, 0)

_, process_id = win32process.GetWindowThreadProcessId(hWnd)
# Open the process with necessary access rights
h_process = win32api.OpenProcess(win32con.PROCESS_VM_READ | win32con.PROCESS_VM_WRITE | win32con.PROCESS_VM_OPERATION, False, process_id)
# Allocate memory in the process
h_buffer = win32process.VirtualAllocEx(
    h_process,
    0,
    ctypes.sizeof(TBBUTTON),
    win32con.MEM_COMMIT,
    win32con.PAGE_READWRITE
)

# init our tool bar button and a handle to it
tbButton = TBBUTTON()

def get_icon_dimension(hIcon):
    iconinfo = win32gui.GetIconInfo(hIcon)
    print(iconinfo)
    bmInfo = win32gui.GetObject(iconinfo[3])
    print(bmInfo)
    return bmInfo.bmWidth, bmInfo.bmHeight

for i in range(numIcons):
    tray_item = get_tray_item(i, h_buffer, h_process, hWnd)

    hIcon = tray_item.hIcon

    if hIcon:
        # Get the actual icon dimensions
        icon_width, icon_height = 32,32

        # Create a device context
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, icon_width, icon_height)
        hdc = hdc.CreateCompatibleDC()

        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hIcon)

        bmpstr = hbmp.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGBA',
            (icon_width, icon_height),
            bmpstr, 'raw', 'BGRA', 0, 1
        )

        # Now 'img' is a PIL Image object containing the full icon
        # You can save it or process it further
        img.save(f"tray_icon_{i}.png")

        # Clean up
        win32gui.DeleteObject(hbmp.GetHandle())
        hdc.DeleteDC()
    else:
        print(f"Couldn't get icon for button {i}")
   #  # i leave it to you to get the process from the pid
   #  # that should be trivial...
   #  print(butPid)
