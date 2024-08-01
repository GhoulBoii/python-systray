import ctypes
from tray_struct import TBBUTTON, TrayItem

import commctrl
import win32api
import win32con
import win32gui
import win32process
from helper.icon_extractor import save_icon_as_image

TB_GETBUTTON = 0x417
TBSTATE_HIDDEN = 0x8


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


def main():
    # Find the system tray window
    hWnd = win32gui.FindWindow("Shell_TrayWnd", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "TrayNotifyWnd", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "SysPager", None)
    hWnd = win32gui.FindWindowEx(hWnd, None, "ToolbarWindow32", None)

    # Get the count of icons in the tray
    num_icons = win32api.SendMessage(hWnd, commctrl.TB_BUTTONCOUNT, 0, 0)

    # Get process information
    _, process_id = win32process.GetWindowThreadProcessId(hWnd)
    h_process = win32api.OpenProcess(
        win32con.PROCESS_VM_READ
        | win32con.PROCESS_VM_WRITE
        | win32con.PROCESS_VM_OPERATION,
        False,
        process_id,
    )

    # Allocate memory in the process
    h_buffer = win32process.VirtualAllocEx(
        h_process,
        0,
        ctypes.sizeof(TBBUTTON),
        win32con.MEM_COMMIT,
        win32con.PAGE_READWRITE,
    )

    try:
        for i in range(num_icons):
            tray_item = get_tray_item(i, h_buffer, h_process, hWnd)

            if tray_item.hIcon:
                save_icon_as_image(tray_item.hIcon, f"tray_icon_{i}.png")
            else:
                print(f"Couldn't get icon for button {i}")

    finally:
        # Clean up
        try:
            win32process.VirtualFreeEx(h_process, h_buffer, 0, win32con.MEM_RELEASE)
        except Exception as e:
            print(f"Error freeing memory: {e}")

        try:
            win32api.CloseHandle(h_process)
        except Exception as e:
            print(f"Error closing handle: {e}")


if __name__ == "__main__":
    main()
