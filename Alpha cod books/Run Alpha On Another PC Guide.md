# Run Alpha On Another PC Guide

This guide explains how to run the full `Code;ALPHA` project from a pen drive or copied folder on another Windows PC.

## Best Way To Move The Project

You can carry the full `Code;ALPHA` folder on a pen drive.

Best practice:
- copy the full folder from the pen drive to a normal folder on the other PC
- keep all inner folder names exactly the same
- do not rename folders like `Maine File`, `Rouls File`, `Libary`, `Packages`, or `Alpha learner`

Why this is better:
- Alpha writes database files, user files, and project files
- some PCs block writing to removable drives
- a local folder is faster and safer than running everything directly from the pen drive

## What The Other PC Needs

Install these on the other Windows PC:

1. `Python 3.11` or newer
2. A modern browser like `Chrome`, `Edge`, or `Firefox`
3. A normal Python install which includes `tkinter`

Important during Python install:
- turn on `Add Python to PATH`

For phone and local Wi-Fi sharing:
- allow Python through Windows Firewall when asked

For Android APK building only:
- install `Android Studio`
- install the Android SDK
- install Java / JDK if Android Studio asks for it

## First Check On The Other PC

Open PowerShell inside the copied `Code;ALPHA` folder and run:

```powershell
python --version
```

If Python is installed correctly, you should see a Python version number.

If `python` is not found:
- reinstall Python from `python.org`
- make sure `Add Python to PATH` is enabled
- reopen PowerShell after installation

## Main Alpha Passwords

These startup passwords are used in the project:

- Alpha Studio server password: `aritra1234`
- Alpha desktop software password: `aritra1234`

## Run The Main Alpha Programs

Open PowerShell in the main project folder and use these commands.

### Run Alpha Studio

```powershell
python "Maine File/maine.py"
```

Then open:

`http://127.0.0.1:8080`

### Run Alpha Studio For Phone And PC Together

```powershell
python "Maine File/maine.py" --share-lan
```

Then open the printed `192.168...` address on devices connected to the same trusted Wi-Fi.

### Run Alpha Learn

```powershell
python "Alpha learner/learn_server.py"
```

Then open:

`http://127.0.0.1:8110`

### Run Alpha Learn For Phone And PC Together

```powershell
python "Alpha learner/learn_server.py" --share-lan
```

### Run Alpha Kids

```powershell
python "kids frendly alpha/kids_server.py"
```

Then open:

`http://127.0.0.1:8090`

### Run Alpha Website Logic Engine

```powershell
python "Alpha Website Logic Engine/engine_server.py"
```

Then open:

`http://127.0.0.1:8095`

### Run Alpha Desktop Software

```powershell
python "alpha_language_sistem_softower/alpha_desktop_software.py"
```

This needs a standard Python installation with `tkinter`.

## Run Alpha Files Directly

You can also run Alpha source files directly from the interpreter.

Example:

```powershell
python "Maine File/alpha.py" "Examples/class_demo.alpha"
```

More examples:
- `Examples/database_demo.alpha`
- `Examples/function_report_demo.alpha`
- `Examples/random_time_demo.alpha`
- `Examples/class_demo.alpha`

## What Usually Works Without Extra Pip Packages

The main Alpha project is built so it does not need normal third-party `pip` packages for the core browser platforms.

That means these usually work after Python is installed:
- Alpha Studio
- Alpha Learn
- Alpha Kids
- Alpha Website Logic Engine
- direct Alpha file runs

## Important Folder Behavior

Alpha uses these folders while running:

- `alpha_user_data` for saved users and projects
- `Libary` for the Alpha SQLite database
- `Examples` for sample Alpha programs
- `reports` and `notes` for file-writing examples

Do not delete these unless you want to clear saved data or generated files.

## Android APK Project Note

The folder:

`alpha mobile coder studio apk`

is an Android Studio project.

Important:
- it is not automatically a ready-made APK on every PC
- you must open that folder in Android Studio and build the APK there
- the built debug APK will usually appear in:

`app/build/outputs/apk/debug/app-debug.apk`

## Common Problems And Fixes

### Problem: `python` command is not working

Fix:
- install Python again
- enable `Add Python to PATH`
- close and reopen PowerShell

### Problem: browser page does not open

Fix:
- make sure the server command is still running
- open the exact local URL shown in the terminal
- try `Ctrl + F5` in the browser

### Problem: phone cannot connect

Fix:
- use `--share-lan`
- keep phone and PC on the same Wi-Fi
- allow Python through Windows Firewall
- open the printed `192.168...` address, not `127.0.0.1`

### Problem: desktop software does not open

Fix:
- use a normal Python install with `tkinter`
- do not use a stripped-down Python build

### Problem: project files cannot save

Fix:
- copy the folder from the pen drive to the PC first
- make sure the folder is not read-only
- avoid running the full project from a locked removable drive

## Recommended Setup Order On Another PC

1. Copy the full `Code;ALPHA` folder to the new PC
2. Install Python 3.11+ with PATH enabled
3. Test `python --version`
4. Run `python "Maine File/maine.py"`
5. Enter the password `aritra1234`
6. Open Alpha Studio in the browser
7. Run Alpha Learn, Kids, Website Logic Engine, or desktop software as needed

## Short Safe Recommendation

For the smoothest experience on another PC:
- copy the folder to the local disk
- install normal Python 3.11+
- use the browser products first
- use the desktop software only after confirming `tkinter` works
