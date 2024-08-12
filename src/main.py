import tkinter as tk
import win32con
import win32gui
from PIL import ImageTk
import utils.tray_getter as tget


class TrayIconViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Tray Icons")
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.icons = []
        self.canvas_images = []
        self.double_click_time = win32gui.GetDoubleClickTime()

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

    def update_icons(self):
        self.icons = tget.get_tray_items()
        self.draw_icons()

    def on_left_click(self, event):
        self.handle_click(event, win32con.WM_LBUTTONUP)

    def on_right_click(self, event):
        self.handle_click(event, win32con.WM_RBUTTONUP)

    def on_left_double_click(self, event):
        self.handle_click(event, win32con.WM_LBUTTONDBLCLK)

    def on_right_double_click(self, event):
        self.handle_click(event, win32con.WM_RBUTTONDBLCLK)

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
                        lparam = event.x | (event.y << 16)

                        if message in (
                            win32con.WM_LBUTTONUP,
                            win32con.WM_LBUTTONDBLCLK,
                        ):
                            click_type = "Left"
                        else:
                            click_type = "Right"

                        if message == win32con.WM_RBUTTONUP:
                            icon.send_message(win32con.WM_RBUTTONDOWN, lparam)

                        if (
                            icon.handle_left_click
                            or icon.handle_right_click < self.double_click_time
                        ):
                            print(f"Double {click_type.lower()} click detected!")
                        else:
                            print(f"Single {click_type.lower()} click detected.")

                        result = icon.send_message(message, lparam)

                        print(f"Clicking icon: {icon.title}")
                        print("version: ", icon.version)
                        print("Message hiword: ", icon.get_message_hiword())
                        print("Lparam: ", lparam)
                        print(f"Message sent: {result}")
                        return

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

    def setup_bindings(self):
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_left_double_click)
        self.canvas.bind("<Double-Button-3>", self.on_right_double_click)

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
