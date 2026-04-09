# Alpha Learn

Alpha Learn is a beginner coding platform for Alpha's human-readable syntax.

It is a separate browser product focused on:
- step-by-step lessons
- track-based learning
- a real Alpha code lab
- glossary and quiz support
- local progress tracking in the browser

## Run Alpha Learn

```powershell
python "Alpha learner/learn_server.py"
```

Open:

`http://127.0.0.1:8110`

To open it on a phone or another PC on the same trusted Wi-Fi:

```powershell
python "Alpha learner/learn_server.py" --share-lan
```

Then open the printed `192.168...` address on the other device.

## What It Includes

- beginner lesson tracks
- Alpha editor with syntax highlighting
- run output and translated runtime execution through the real Alpha interpreter
- quiz cards
- glossary cards
- quick-win starter projects
- progress badges and browser-saved completion

## Notes

- Progress is stored in the browser through local storage.
- The main Alpha Studio is unchanged.
- Alpha Learn is for teaching and practice, while the main studio remains the full development workspace.
