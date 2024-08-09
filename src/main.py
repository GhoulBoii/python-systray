import ctypes
from tray_struct import TBBUTTON, TrayItem

import commctrl
import win32api
import win32con
import win32gui
import win32process

import utils.icon as icon_util
import tkinter as tk

import win32gui
import win32ui
from PIL import Image, ImageTk

TB_GETBUTTON = 0x417
TBSTATE_HIDDEN = 0x8


class NotifyIcon:
    def __init__(self, hwnd, uid, icon, title, version, callback_message):
        self.hwnd = hwnd
        self.uid = uid
        self.icon = icon
        self.title = title
        self.version = version
        self.callback_message = callback_message

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


class TrayIconViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Tray Icons")
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.icons = []
        self.canvas_images = []

    def get_tray_item(self, i, h_buffer, h_process, toolbar_hwnd):
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

    def get_tray_items(self) -> list:
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
            tray_item = self.get_tray_item(i, h_buffer, h_process, hWnd)

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

    def update_icons(self):
        self.icons = self.get_tray_items()
        self.draw_icons()

    def draw_icons(self):
        self.canvas.delete("all")
        self.canvas_images.clear()

        x_offset = 10
        y_offset = 10
        for icon in self.icons:
            photo_image = ImageTk.PhotoImage(icon.icon)
            self.canvas_images.append(photo_image)
            self.canvas.create_image(
                x_offset,
                y_offset,
                anchor="nw",
                image=photo_image,
                tags=(f"icon_{icon.uid}",),
            )
            x_offset += 40
            if x_offset > self.canvas.winfo_width() - 40:
                x_offset = 10
                y_offset += 40

        self.canvas.update()

    def setup_bindings(self):
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

    def on_mouse_move(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("icon_"):
                    uid = int(tag.split("_")[1])
                    icon = next((i for i in self.icons if i.uid == uid), None)
                    if icon:
                        self.root.title(f"Icon: {icon.title}")
                    return
        self.root.title("System Tray Icons")

    def on_left_click(self, event):
        self.handle_click(event, win32con.WM_LBUTTONUP)

    def on_right_click(self, event):
        self.handle_click(event, win32con.WM_RBUTTONUP)

    def handle_click(self, event, message):
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("icon_"):
                    uid = int(tag.split("_")[1])
                    icon = next((i for i in self.icons if i.uid == uid), None)
                    if icon:
                        print(f"Clicking icon: {icon.title}")
                        # Convert mouse position to LPARAM format
                        lparam = event.x | (event.y << 16)
                        result = icon.send_message(message, lparam)
                        print(f"Message sent: {result}")
                        return

    def start(self):
        self.setup_bindings()
        self.update_icons()
        self.root.after(500, self.periodic_update)
        self.root.mainloop()

    def periodic_update(self):
        self.update_icons()
        self.root.after(500, self.periodic_update)


if __name__ == "__main__":
    viewer = TrayIconViewer()
    viewer.start()
