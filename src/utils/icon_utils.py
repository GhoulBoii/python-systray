import win32gui
import win32ui
from PIL import Image


def get_dimension(hIcon):
    """
    Get the dimensions of an icon.
    """
    iconinfo = win32gui.GetIconInfo(hIcon)
    bmInfo = win32gui.GetObject(iconinfo[3])
    return bmInfo.bmWidth, bmInfo.bmHeight


def get_image(hIcon):
    icon_width, icon_height = (32, 32)

    # Create a device context
    hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    hbmp = win32ui.CreateBitmap()
    hbmp.CreateCompatibleBitmap(hdc, icon_width, icon_height)
    hdc = hdc.CreateCompatibleDC()

    hdc.SelectObject(hbmp)
    hdc.DrawIcon((0, 0), hIcon)

    bmpstr = hbmp.GetBitmapBits(True)

    image = Image.frombuffer(
        "RGBA", (icon_width, icon_height), bmpstr, "raw", "BGRA", 0, 1
    )

    # Clean up
    win32gui.DeleteObject(hbmp.GetHandle())
    hdc.DeleteDC()

    return image


def save_images(images, filename):
    """
    Save an icon as an image file.
    """
    for image in images:
        image.save(filename)
