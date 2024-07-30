import commctrl, win32con
import win32api
import win32gui
import win32process
from ctypes import *
import ctypes as c
from ctypes import wintypes as w


# represent the TBBUTTON structure
# note this is 32 bit, 64 bit padds 4 more reserved bytes
class TBBUTTON(Structure):
    _fields_ = [
        ('iBitmap', c_int),
        ('idCommand', c_int),
        ('fsState', c_byte),
        ('fsStyle', c_byte),
        ('bReserved', c_ubyte * 6),
        ('dwData', c_ulong),
        ('iString', c_int),
    ]

k32 = WinDLL('kernel32', use_last_error=True)
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = w.HANDLE,w.LPCVOID,w.LPVOID,c.c_size_t,c.POINTER(c.c_size_t)
ReadProcessMemory.restype = w.BOOL

# get the handle to the sytem tray
hWnd = win32gui.FindWindow("Shell_TrayWnd", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "TrayNotifyWnd", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "SysPager", None)
hWnd = win32gui.FindWindowEx(hWnd, None, "ToolbarWindow32", None)

# get the count of icons in the tray
numIcons = win32api.SendMessage(hWnd, commctrl.TB_BUTTONCOUNT, 0, 0)

# allocate memory within the system tray
pid = c_ulong();
windll.user32.GetWindowThreadProcessId(hWnd, byref(pid))
hProcess = windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, 0, pid)
lpPointer = windll.kernel32.VirtualAllocEx(hProcess, 0, sizeof(TBBUTTON), win32con.MEM_COMMIT, win32con.PAGE_READWRITE)

# init our tool bar button and a handle to it
tbButton = TBBUTTON()
butHandle = c_int()

for i in range(numIcons):
    # query the button into the memory we allocated
    windll.user32.SendMessageA(hWnd, commctrl.TB_GETBUTTON, i, lpPointer)
    # read the memory into our button struct
    ReadProcessMemory(hProcess, lpPointer, addressof(tbButton), sizeof(tbButton), None)
    # read the 1st 4 bytes from the dwData into the butHandle var
    # these first 4 bytes contain the handle to the button
    ReadProcessMemory(hProcess, tbButton.dwData, addressof(butHandle), sizeof(tbButton), None)

    # get the pid that created the button
    butPid = c_ulong()
    windll.user32.GetWindowThreadProcessId(butHandle, byref(butPid))

    # i leave it to you to get the process from the pid
    # that should be trivial...
    print(butPid)
