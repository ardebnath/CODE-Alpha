# Alpha Language System Software

This folder contains the desktop software version of Alpha.

## What It Includes

- a desktop Alpha code editor
- run output and translated Python panels
- starter programs and language guide pages
- package manager controls
- recent run history
- error line highlighting in the editor

## Main File

- `alpha_desktop_software.py`

## How To Run

Use Python 3.11 or newer:

```powershell
python "alpha_language_sistem_softower/alpha_desktop_software.py"
```

Or use the launcher:

```powershell
alpha_language_sistem_softower\run_alpha_software.bat
```

## Shortcuts

- `Ctrl + Enter` runs Alpha code
- `Ctrl + S` saves the current file
- `Ctrl + O` opens an Alpha file

## Notes

- this desktop software uses the main Alpha runtime from `Maine File/alpha.py`
- sample programs come from the Alpha rules file
- package state and run history use the same Alpha database as the rest of the project
- use a standard Python build that includes `tkinter`; some embedded Python runtimes do not include it
