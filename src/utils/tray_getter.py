import ctypes

import commctrl
import utils.icon_utils as icon_util
import win32api
import win32con
import win32gui
import win32process
from utils.tray_struct import TBBUTTON, NotifyIcon, TrayItem

TB_GETBUTTON = 0x417
TBSTATE_HIDDEN = 0x8
IGNORED_GUIDS = {
    "7820ae76-23e3-4229-82c1-e41cb67d5b9c",  # HEALTH_GUID
    "7820ae83-23e3-4229-82c1-e41cb67d5b9c",  # MEETNOW_GUID
    "7820ae74-23e3-4229-82c1-e41cb67d5b9c",  # NETWORK_GUID
    "7820ae75-23e3-4229-82c1-e41cb67d5b9c",  # POWER_GUID
    "7820ae73-23e3-4229-82c1-e41cb67d5b9c",  # VOLUME_GUID
}


def get_tray_item(i, h_buffer, h_process, toolbar_hwnd):
    """
    Retrieve a TrayItem from the system tray.
    """
    tb_button = TBBUTTON()
    tray_item = TrayItem()

    # Send message to get button information
    win32gui.SendMessage(toolbar_hwnd, TB_GETBUTTON, i, h_buffer)

    # Read the memory into our button struct
    button_info_buffer = win32process.ReadProcessMemory(
        h_process, h_buffer, ctypes.sizeof(TBBUTTON)
    )
    ctypes.memmove(
        ctypes.addressof(tb_button), button_info_buffer, ctypes.sizeof(TBBUTTON)
    )

    if tb_button.dwData != 0:
        # Read the TrayItem data
        tray_item_buffer = win32process.ReadProcessMemory(
            h_process, tb_button.dwData, ctypes.sizeof(TrayItem)
        )
        ctypes.memmove(
            ctypes.addressof(tray_item), tray_item_buffer, ctypes.sizeof(TrayItem)
        )

        # Set the state
        tray_item.dwState = 1 if tb_button.fsState & TBSTATE_HIDDEN else 0

        print(f"ExplorerTrayService: Got tray item: {tray_item.szIconText}")

    return tray_item


def get_tray_items() -> list:
    hWnd = win32gui.FindWindow("Shell_TrayWnd", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "TrayNotifyWnd", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "SysPager", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "ToolbarWindow32", None)

    _, process_id = win32process.GetWindowThreadProcessId(hWnd)
    h_process = win32api.OpenProcess(
        win32con.PROCESS_VM_READ
        | win32con.PROCESS_VM_WRITE
        | win32con.PROCESS_VM_OPERATION,
        False,
        process_id,
    )
    h_buffer = win32process.VirtualAllocEx(
        h_process,
        0,
        ctypes.sizeof(TBBUTTON),
        win32con.MEM_COMMIT,
        win32con.PAGE_READWRITE,
    )

    # Get the count of icons in the tray
    num_icons: int = win32api.SendMessage(hWnd, commctrl.TB_BUTTONCOUNT, 0, 0)

    icons = []

    for i in range(num_icons):
        tray_item = get_tray_item(i, h_buffer, h_process, hWnd)

        # Check if the GUID is in the ignored list
        if tray_item.guidItem:
            guid_str = str(tray_item.guidItem_python)
            if guid_str in IGNORED_GUIDS:
                continue

        if tray_item.hIcon:
            icon_image = icon_util.get_image(tray_item.hIcon)
            icons.append(
                NotifyIcon(
                    tray_item.hWnd,
                    tray_item.uID,
                    icon_image,
                    tray_item.szIconText,
                    tray_item.uVersion,
                    tray_item.uCallbackMessage,
                )
            )
        else:
            print(f"Couldn't get icon for button {i}")
    win32api.CloseHandle(h_process)
    return icons
