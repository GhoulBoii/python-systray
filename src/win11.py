import win32gui
import win32con
from comtypes.client import CreateObject
import comtypes.gen.UIAutomationClient as UIAClient

def enum_window_callback(hwnd, results):
    class_name = win32gui.GetClassName(hwnd)
    if class_name == "Shell_TrayWnd":
        results.append(hwnd)

def get_tray_icons():
    print("Starting get_tray_icons function")

    try:
        # Initialize UI Automation
        print("Initializing UI Automation")
        automation = CreateObject(UIAClient.CUIAutomation, interface=UIAClient.IUIAutomation)

        # Find the taskbar
        taskbars = []
        win32gui.EnumWindows(enum_window_callback, taskbars)
        if not taskbars:
            print("Taskbar not found")
            return []

        taskbar = taskbars[0]
        print(f"Found taskbar: {taskbar}")

        # Get the UI Automation element for the taskbar
        taskbar_element = automation.ElementFromHandle(taskbar)

        # Create a condition for finding all elements
        condition = automation.CreateTrueCondition()

        # Find all descendant elements
        print("Finding all descendant elements")
        children = taskbar_element.FindAll(UIAClient.TreeScope_Subtree, condition)

        print(f"Found {children.Length} elements")

        tray_icons = []

        for i in range(children.Length):
            child = children.GetElement(i)
            try:
                name = child.CurrentName
                class_name = child.CurrentClassName
                automation_id = child.CurrentAutomationId
                print(f"Element {i}: Name={name}, Class={class_name}, AutomationID={automation_id}")
                if name and "Button" in class_name and automation_id == "NotifyItemIcon":  # Most tray icons are buttons
                    tray_icons.append({
                        "name": name,
                        "class_name": class_name,
                        "automation_id": automation_id
                    })
            except Exception as e:
                print(f"Error accessing element {i}: {str(e)}")

        print(f"Returning {len(tray_icons)} tray icons")
        return tray_icons
    except Exception as e:
        print(f"Unexpected error in get_tray_icons: {str(e)}")
        return []

print("Starting script")
icons = get_tray_icons()

print("\nFinal results:")
for icon in icons:
    print(f"Icon: {icon['name']}")
    print(f"  Class: {icon['class_name']}")
    print(f"  Automation ID: {icon['automation_id']}")
    print()

print("Script completed")
