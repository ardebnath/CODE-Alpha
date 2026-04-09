# Alpha by Bluear_cod

Alpha is a human-friendly interpreted programming language powered by a Python runtime.

This project includes:
- the Alpha interpreter
- the Alpha Studio web runner
- the Alpha language book
- built-in SQLite storage
- installable local Alpha packages
- mobile and desktop access through the local studio server

## License Status

This project is now described as source-available proprietary material of `Bluear_cod`.
Project owner / brand:
- `Bluear_cod`

License file:
- `LICENSE`

Main project areas:
- `Maine File/alpha.py` -> interpreter runtime
- `Maine File/maine.py` -> local studio server
- `Maine File/index.html` -> browser runner UI
- `Maine File/studio.js` -> browser editor logic
- `Maine File/style.css` -> studio styling
- `Alpha Language Book.md` -> Alpha writing guide
- `Run Alpha On Another PC Guide.md` -> setup and run guide for another Windows PC
- `Commercial Use, Credit, and Source Protection Policy.md` -> draft policy for credit, business use, and source protection

## Quick Start

Run Alpha source:

```powershell
python "Maine File/alpha.py" "Examples/hello.alpha"
```

Run Alpha Studio:

```powershell
python "Maine File/maine.py"
```

Run Alpha Studio for phone + PC on the same trusted Wi-Fi:

```powershell
python "Maine File/maine.py" --share-lan
```

## Patent And Ownership

This repository is branded for `Bluear_cod`.

Important:
- branding a project under a company name does not by itself create a patent
- making a project more patent-ready means documenting inventorship, ownership, filing dates, and technical novelty
- if `Bluear_cod` is the patent owner/applicant, inventors should assign the invention to `Bluear_cod`

Read these project documents:
- `Bluear_cod Patent Readiness Pack.md`
- `Bluear_cod Invention Disclosure.md`
- `Bluear_cod IP Assignment Memo.md`

## Source Visibility

Important:
- HTML, CSS, and JavaScript sent to the browser are never truly secret
- Python code can stay private only if you keep it on your own machine or server
- packaging or obfuscation can slow copying down, but it does not create perfect protection

For full details, read:
- `Alpha Source, Open Source, and Protection Guide.md`
- `Commercial Use, Credit, and Source Protection Policy.md`
