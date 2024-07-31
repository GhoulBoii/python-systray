import commctrl, win32con
import win32api
import win32gui
import win32process
import ctypes
from ctypes import wintypes as w


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

# get the handle to the sytem tray
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

for i in range(numIcons):
    # query the button into the memory we allocated
    win32gui.SendMessage(hWnd, commctrl.TB_GETBUTTON, i, h_buffer)
    button_info_buffer = win32process.ReadProcessMemory(h_process, h_buffer, ctypes.sizeof(TBBUTTON))
    ctypes.memmove(ctypes.addressof(tbButton), button_info_buffer, ctypes.sizeof(TBBUTTON))

    # Read the memory into our button struct
    butHandle = w.DWORD()
    butHandle_buffer = win32process.ReadProcessMemory(h_process, tbButton.dwData, ctypes.sizeof(w.DWORD))
    ctypes.memmove(ctypes.addressof(butHandle), butHandle_buffer, ctypes.sizeof(w.DWORD))

    # get the pid that created the button
    _, butPid = win32process.GetWindowThreadProcessId(butHandle.value)

    # i leave it to you to get the process from the pid
    # that should be trivial...
    print(butPid)
