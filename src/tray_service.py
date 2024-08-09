import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api
from win32com.shell import shell, shellcon
import threading
import time
from typing import Callable, NamedTuple, Optional
from ctypes import Structure, c_uint, c_int, c_void_p
import uuid

# Define necessary structures
class SafeNotifyIconData(Structure):
    pass

class APPBARMSGDATAV3(Structure):
    pass

class TrayHostSizeData(NamedTuple):
    pass

# Define types for the delegates
SystrayDelegate = Callable[[int, SafeNotifyIconData], bool]
IconDataDelegate = Callable[[int, int, int, uuid.UUID], int]
TrayHostSizeDelegate = Callable[[], TrayHostSizeData]
AppBarMessageDelegate = Callable[[APPBARMSGDATAV3, bool], int]

class TrayService:
class TrayService:
    NotifyWndClass = "TrayNotifyWnd"
    TrayWndClass = "Shell_TrayWnd"

    def __init__(self):
        self.hwnd_tray = 0
        self.hwnd_notify = 0
        self.hwnd_fwd = 0
        self.tray_monitor = None
        self.wnd_class = None
        self.systray_callback: Optional[SystrayDelegate] = None
        self.icon_data_callback: Optional[IconDataDelegate] = None
        self.tray_host_size_callback: Optional[TrayHostSizeDelegate] = None
        self.app_bar_message_callback: Optional[AppBarMessageDelegate] = None

    def initialize(self):
        if self.hwnd_tray:
            return self.hwnd_tray

        self.destroy_windows()
        self.register_tray_wnd()
        self.register_notify_wnd()

        return self.hwnd_tray

    def __init__(self):

    def set_systray_callback(self, callback: SystrayDelegate):
        self.systray_callback = callback

    def set_icon_data_callback(self, callback: IconDataDelegate):
        self.icon_data_callback = callback

    def set_tray_host_size_callback(self, callback: TrayHostSizeDelegate):
        self.tray_host_size_callback = callback

    def set_app_bar_message_callback(self, callback: AppBarMessageDelegate):
        self.app_bar_message_callback = callback

    # Example of how to use these callbacks
    def handle_systray_message(self, msg: int, nic_data: SafeNotifyIconData) -> bool:
        if self.systray_callback:
            return self.systray_callback(msg, nic_data)
        return False

    def handle_icon_data_message(self, dw_message: int, h_wnd: int, u_id: int, guid_item: uuid.UUID) -> int:
        if self.icon_data_callback:
            return self.icon_data_callback(dw_message, h_wnd, u_id, guid_item)
        return 0

    def get_tray_host_size(self) -> TrayHostSizeData:
        if self.tray_host_size_callback:
            return self.tray_host_size_callback()
        return TrayHostSizeData()  # Return a default value if no callback is set

    def handle_app_bar_message(self, amd: APPBARMSGDATAV3) -> int:
        if self.app_bar_message_callback:
            handled = False
            result = self.app_bar_message_callback(amd, handled)
            return result if handled else 0
        return 0
    def run(self):
        if self.hwnd_tray:
            self.resume()
            self.send_taskbar_created()

    def suspend(self):
        if self.hwnd_tray:
            if self.tray_monitor:
                self.tray_monitor.cancel()
            ctypes.windll.user32.SetWindowPos(
                self.hwnd_tray, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE
            )

    def resume(self):
        if self.hwnd_tray:
            self.set_windows_tray_bottommost()
            self.make_tray_topmost()
            self.start_tray_monitor()

    def send_taskbar_created(self):
        msg = win32gui.RegisterWindowMessage("TaskbarCreated")
        if msg:
            print("TrayService: Sending TaskbarCreated message")
            ctypes.windll.user32.SendNotifyMessageW(win32con.HWND_BROADCAST, msg, 0, 0)

    def destroy_windows(self):
        if self.hwnd_notify:
            win32gui.DestroyWindow(self.hwnd_notify)
            win32gui.UnregisterClass(self.NotifyWndClass, None)
            print(f"TrayService: Unregistered {self.NotifyWndClass}")

        if self.hwnd_tray:
            win32gui.DestroyWindow(self.hwnd_tray)
            win32gui.UnregisterClass(self.TrayWndClass, None)
            print(f"TrayService: Unregistered {self.TrayWndClass}")

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_COPYDATA:
            # Handle WM_COPYDATA message
            pass
        elif msg == win32con.WM_WINDOWPOSCHANGED:
            # Handle WM_WINDOWPOSCHANGED message
            pass

        if msg in [win32con.WM_COPYDATA, win32con.WM_ACTIVATEAPP, win32con.WM_COMMAND] or msg >= win32con.WM_USER:
            return self.forward_msg(hwnd, msg, wparam, lparam)

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def forward_msg(self, hwnd, msg, wparam, lparam):
        if not self.hwnd_fwd or not win32gui.IsWindow(self.hwnd_fwd):
            self.hwnd_fwd = self.find_windows_tray(self.hwnd_tray)

        if self.hwnd_fwd:
            return win32gui.SendMessage(self.hwnd_fwd, msg, wparam, lparam)

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def register_tray_wnd(self):
        wnd_class = win32gui.WNDCLASS()
        wnd_class.lpszClassName = self.TrayWndClass
        wnd_class.hInstance = win32api.GetModuleHandle(None)
        wnd_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wnd_class.lpfnWndProc = self.wnd_proc

        class_atom = win32gui.RegisterClass(wnd_class)
        self.wnd_class = wnd_class

        style = win32con.WS_POPUP | win32con.WS_CLIPCHILDREN | win32con.WS_CLIPSIBLINGS
        exstyle = win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW

        self.hwnd_tray = win32gui.CreateWindowEx(
            exstyle, class_atom, "", style, 0, 0,
            win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
            int(23 * self.get_dpi_scale()), 0, 0, wnd_class.hInstance, None
        )

        if not self.hwnd_tray:
            print(f"TrayService: Error creating {self.TrayWndClass} window")
        else:
            print(f"TrayService: Created {self.TrayWndClass}")

    def register_notify_wnd(self):
        # Similar to register_tray_wnd, but for NotifyWndClass
        pass

    def start_tray_monitor(self):
        self.tray_monitor = threading.Timer(0.1, self.tray_monitor_tick)
        self.tray_monitor.start()

    def tray_monitor_tick(self):
        if not self.hwnd_tray:
            return

        taskbar_hwnd = win32gui.FindWindow(self.TrayWndClass, "")

        if taskbar_hwnd != self.hwnd_tray:
            print("TrayService: Raising Shell_TrayWnd")
            self.make_tray_topmost()

        self.start_tray_monitor()

    def set_windows_tray_bottommost(self):
        taskbar_hwnd = self.find_windows_tray(self.hwnd_tray)
        if taskbar_hwnd:
            win32gui.SetWindowPos(
                taskbar_hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )

    def make_tray_topmost(self):
        if self.hwnd_tray:
            win32gui.SetWindowPos(
                self.hwnd_tray, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE
            )

    @staticmethod
    def find_windows_tray(exclude_hwnd):
        def enum_windows_proc(hwnd, results):
            if win32gui.GetClassName(hwnd) == TrayService.TrayWndClass and hwnd != exclude_hwnd:
                results.append(hwnd)
            return True

        results = []
        win32gui.EnumWindows(enum_windows_proc, results)
        return results[0] if results else None

    @staticmethod
    def get_dpi_scale():
        # This is a simplified version. You might need to use actual DPI awareness APIs
        return ctypes.windll.user32.GetDpiForSystem() / 96.0

# Usage
if __name__ == "__main__":
    tray_service = TrayService()
    tray_service.initialize()
    tray_service.run()

    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
