import sys
import os
import subprocess

def pack_assistent(workspace_path):
    # Check if the workspace path exists
    if not os.path.exists(workspace_path):
        print(f"Error: Workspace path '{workspace_path}' does not exist.")
        return

    # Build PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--windowed",
        "--add-data",
        f'{os.path.join(workspace_path, "app", "config")};app/config',
        "--icon",
        f'{os.path.join(workspace_path, "app", "resource", "images", "logo.png")}',
        os.path.join(workspace_path, "Assistent.py")
    ]

    # Execute the command
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("PyInstaller command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing PyInstaller command: {e}")

if __name__ == "__main__":
    # Get the WORKSPACE path from the command line argument
    if len(sys.argv) != 2:
        print("Usage: python pack_assistent.py <WORKSPACE_PATH>")
    else:
        workspace_arg = sys.argv[1]
        pack_assistent(workspace_arg)
