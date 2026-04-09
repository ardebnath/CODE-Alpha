# Update Hear

## Purpose

This book tracks the updates integrated into Alpha.

Each update entry includes:
- date
- time
- importance
- what it updated
- what it fixed
- update details

This book is focused on Alpha language and runtime updates.
It does not replace the main Alpha language book.

---

## Update Entry 1

- Date: 2026-04-01
- Time: earlier development session (exact time not captured)
- Importance: Critical
- What It Updated: Core Alpha language, interpreter, runtime, and SQLite-backed storage
- What It Fixed: Alpha moved from empty starter files into a working interpreted language
- Update Details:
  - added the Alpha translator and runtime
  - added variables, output, loops, conditions, functions, and error handling
  - added safe imports
  - added SQLite storage helpers such as `store`, `fetch`, `records`, and `history`
  - added the first Alpha book and starter examples

## Update Entry 2

- Date: 2026-04-01
- Time: earlier development session (exact time not captured)
- Importance: High
- What It Updated: Alpha Studio, browser runner, package system, mobile support, and Turtle support
- What It Fixed: Alpha became usable from the browser and easier to extend
- Update Details:
  - added Alpha Studio with editor, output, translated Python view, and history
  - added syntax highlighting and autosave
  - added local package management
  - added mobile and desktop shared studio support
  - added Turtle graphics support
  - added package examples and runtime samples

## Update Entry 3

- Date: 2026-04-01
- Time: earlier development session (exact time not captured)
- Importance: High
- What It Updated: Project ownership, open-source status, and source-visibility documentation
- What It Fixed: Project legal/release position became documented and clearer
- Update Details:
  - branded the project for `Bluear_cod`
  - added the MIT license
  - added source/open-source/protection guidance
  - added patent-readiness support documents
  - added ownership notes in the main book and runner

## Update Entry 4

- Date: 2026-04-02
- Time: 15:42:47 +05:30
- Importance: Critical
- What It Updated: Alpha language runtime upgrade without changing the UI
- What It Fixed: Alpha gained stronger validation, date/time utilities, CSV helpers, and better data helpers
- Update Details:
  - added `assert` statement support
  - added `raise` statement support with Alpha runtime errors
  - added `current_date()`
  - added `current_time()`
  - added `current_datetime()`
  - added `timestamp_text()`
  - added `sleep_ms(milliseconds)`
  - added `random_choice(items)`
  - added `random_number(start, end)`
  - added `sort_items(items, reverse=false)`
  - added `reverse_items(items)`
  - added `read_csv_rows(path)`
  - added `write_csv_rows(path, rows, headers=nothing)`
  - added `runtime_upgrade_demo` sample code
  - kept the UI unchanged as requested

## Update Entry 5

- Date: 2026-04-02
- Time: 16:00:26 +05:30
- Importance: Medium
- What It Updated: Alpha example library and built-in sample collection
- What It Fixed: Alpha now has broader learning examples for common coding tasks
- Update Details:
  - added `file_demo.alpha`
  - added `error_demo.alpha`
  - added `csv_report_demo.alpha`
  - added `alias_demo.alpha`
  - added `random_time_demo.alpha`
  - added matching built-in sample entries in the Alpha sample registry
  - improved example coverage for files, CSV, aliases, random values, time helpers, and error handling

## Update Entry 6

- Date: 2026-04-02
- Time: 16:04:03 +05:30
- Importance: Medium
- What It Updated: Starter Programs window sample library
- What It Fixed: Alpha Starter Programs now includes more learning and demo programs directly in the sample window
- Update Details:
  - added `json_demo`
  - added `package_alias_demo`
  - added `function_report_demo`
  - added `context_file_demo`
  - added matching `.alpha` example files
  - no UI code was changed because the Starter Programs window reads from the Alpha sample registry

## Update Entry 7

- Date: 2026-04-02
- Time: 16:26:51 +05:30
- Importance: High
- What It Updated: Alpha Studio service worker cache behavior
- What It Fixed: Starter Programs window could stay stale after new examples were added
- Update Details:
  - updated the service worker cache version
  - stopped caching `/api/` responses
  - ensured Starter Programs, package lists, and history use fresh network data
  - kept the UI unchanged

## Update Entry 8

- Date: 2026-04-02
- Time: 16:33:45 +05:30
- Importance: High
- What It Updated: Alpha comment syntax
- What It Fixed: Alpha now supports readable message/comment blocks using `$` and `$$`
- Update Details:
  - added `$` support for one-line comments
  - added `$$ ... $$` support for multi-line comments
  - kept comment parsing safe when `$` appears inside strings
  - added `comment_demo` sample program
  - updated the Alpha Language Book comment section

## Update Entry 9

- Date: 2026-04-02
- Time: 16:49:28 +05:30
- Importance: High
- What It Updated: Alpha error location reporting and editor underline feedback
- What It Fixed: When Alpha code is wrong, the editor can now underline the line where the error happened
- Update Details:
  - added source-line mapping from translated Python back to Alpha source
  - added structured error line and column fields in Alpha run results
  - added runtime traceback mapping for Alpha execution errors
  - added syntax error line mapping
  - added red underline feedback in the editor for the wrong line
  - added line number highlighting for the wrong line

## Update Entry 10

- Date: 2026-04-02
- Time: 17:28:17 +05:30
- Importance: High
- What It Updated: Alpha Studio tabbed layout, motion system, and glass-style visual polish
- What It Fixed: The studio was visually crowded, and workspace, guide, packages, and history now have clearer separation
- Update Details:
  - added a top studio menu bar with dedicated tabs
  - separated Workspace, Guide, Packages, and History into their own tab panels
  - added tab opening and closing animation
  - unified panel colors and glass-style formatting across the studio
  - kept the editor, package manager, guide loader, and history APIs working in the new layout
  - updated the service worker cache version so the new shell can refresh cleanly

## Update Entry 11

- Date: 2026-04-02
- Time: 17:38:34 +05:30
- Importance: High
- What It Updated: Alpha Studio top menu bar visibility and shell refresh behavior
- What It Fixed: The new menu bar could remain hidden in an older cached studio shell and was not visible enough as a true top navigation bar
- Update Details:
  - replaced the earlier menu section with a real top menu bar
  - kept Workspace, Guide, Packages, and History in separate tabs
  - made the top menu sticky so it stays visible while scrolling
  - added versioned front-end asset URLs for the HTML shell
  - updated service worker behavior to fetch fresh shell files first
  - added service worker skip-waiting and auto-reload support for shell updates

## Update Entry 12

- Date: 2026-04-02
- Time: 18:19:18 +05:30
- Importance: High
- What It Updated: Alpha desktop software folder and desktop application layer
- What It Fixed: Alpha now has a real software app in `alpha_language_sistem_softower` instead of only a browser studio
- Update Details:
  - added `alpha_desktop_software.py` as a desktop Alpha application
  - added workspace, guide, packages, and history tabs in the desktop app
  - added file open and save actions for `.alpha` files
  - added desktop run output, translated Python, and issue panels
  - added package install and remove actions in the desktop software
  - added a run-history viewer with source snapshots for the current session
  - added `run_alpha_software.bat` for easier launching
  - added `build_windows_exe.bat` as an optional Windows packaging helper
  - added a local README for the software folder

## Update Entry 13

- Date: 2026-04-06
- Time: 17:40:04 +05:30
- Importance: High
- What It Updated: Desktop software redesign and styling for `alpha_language_sistem_softower`
- What It Fixed: The desktop software layout looked too plain, and it now uses a stronger Alpha visual system with the same project color format
- Update Details:
  - redesigned the desktop software header into a richer hero section
  - added live metric cards for samples, packages, history, and runtime
  - improved tab and button styling while keeping the Alpha color palette
  - upgraded the status area into a stronger colored status badge
  - improved list, detail, and split-panel layout in packages and history
  - polished workspace and result areas with clearer section descriptions
  - kept the same runtime features and desktop software behavior intact

## Update Entry 14

- Date: 2026-04-06
- Time: 17:53:35 +05:30
- Importance: High
- What It Updated: Desktop software layout alignment with `index.html`
- What It Fixed: The previous desktop redesign still did not feel close enough to the Alpha web studio, and the software now follows the same shell structure more directly
- Update Details:
  - replaced the old desktop notebook shell with a web-studio-style custom top menu
  - aligned the desktop software with hero, live banner, studio menu, page stack, and footer sections
  - changed Workspace, Guide, Packages, and History into custom menu-driven pages
  - rebuilt the Guide page into a card grid closer to the web studio layout
  - improved package and history views to match the card-based desktop shell
  - kept the same Alpha runtime actions while making the UI feel closer to `index.html`

## Update Entry 15

- Date: 2026-04-06
- Time: 17:57:19 +05:30
- Importance: Medium
- What It Updated: Desktop software style rollback in `alpha_language_sistem_softower`
- What It Fixed: The `index.html`-style desktop shell was not preferred, and the software was returned to the previous styled desktop version
- Update Details:
  - removed the custom web-studio-style top shell from the desktop app
  - restored the previous desktop notebook layout
  - restored the earlier Guide tab structure
  - kept the richer header, metric cards, status styling, and split package/history panels
  - kept the Alpha runtime behavior unchanged while returning to the previous desktop style

## Update Entry 16

- Date: 2026-04-07
- Time: 10:58:13 +05:30
- Importance: High
- What It Updated: Startup password security for the server runner and desktop software
- What It Fixed: Alpha now asks for a password before the Python server or desktop software can open
- Update Details:
  - added a startup password gate to `Maine File/maine.py`
  - added a startup password dialog to `alpha_language_sistem_softower/alpha_desktop_software.py`
  - set the current startup password to `aritra1234`
  - limited startup access to three attempts before exit
  - kept the rest of the Alpha runtime and UI behavior unchanged

## Update Entry 17

- Date: 2026-04-07
- Time: 11:15:37 +05:30
- Importance: Medium
- What It Updated: Goal checklist verification
- What It Fixed: The goal checklist now reflects a verified project state instead of only unchecked assumptions
- Update Details:
  - verified the goal checklist against the current project files
  - confirmed the language book, browser studio, desktop software, package manager, and open-source documents exist
  - compile-checked the main Python entry points
  - smoke-tested the Alpha interpreter with a simple `note` program
  - added a verification header to `Goll chack mark file/chackmark.taxt`

## Update Entry 18

- Date: 2026-04-07
- Time: 11:21:12 +05:30
- Importance: High
- What It Updated: Class and object support in the Alpha language runtime
- What It Fixed: Alpha can now define reusable objects and inheritance blocks for bigger software instead of relying only on free functions and data structures
- Update Details:
  - added `class` block support to the Alpha translator
  - added readable inheritance syntax with `class Student extends Person`
  - added safe object helpers such as `getattr`, `setattr`, `hasattr`, `isinstance`, `issubclass`, `object`, and `super`
  - added a `Class Demo` starter program in the sample registry
  - added `Examples/class_demo.alpha` as a real object-oriented Alpha example
  - updated the Alpha language book with a new classes and objects section
  - updated the goal checklist to mark class support as complete
  - updated editor keyword highlighting so `class` is shown as an Alpha keyword

## Update Entry 19

- Date: 2026-04-07
- Time: 11:21:12 +05:30
- Importance: High
- What It Updated: Browser studio user accounts, passwords, and personal project save/load
- What It Fixed: Alpha Studio can now keep different users with different passwords and save each user's Alpha projects inside a separate local user folder
- Update Details:
  - added local account registration and login routes to `Maine File/maine.py`
  - added hashed password storage with per-user salts instead of plain-text browser studio passwords
  - added password-change support for signed-in users
  - added session-token handling for browser studio account actions
  - added `alpha_user_data/users/<username>/projects` storage folders for personal saved projects
  - added browser studio save, load, refresh, and delete project actions
  - added account and saved-project panels to the browser studio UI
  - added `alpha_user_data/README.md` to explain the new local user-data folder
  - updated the Alpha language book and checklist for this new studio feature

## Update Entry 20

- Date: 2026-04-07
- Time: 12:04:36 +05:30
- Importance: High
- What It Updated: A separate kids-friendly browser studio in the `kids frendly alpha` folder
- What It Fixed: Alpha now has a playful browser studio for children with simpler lessons, voice help, and easy starter builders without changing the main studio
- Update Details:
  - added `kids frendly alpha/kids_server.py` as a standalone kids browser server
  - added a new kids HTML layout with lesson cards, builder cards, and helper panels
  - added bright responsive styling for a child-friendly coding space
  - added browser speech help for reading lessons and output aloud
  - added simple kid-friendly error explanations in the browser
  - added local lesson progress tracking in the browser
  - added five starter lessons and four project builders for beginners
  - added a README and app shell files for the new kids studio folder

## Update Entry 21

- Date: 2026-04-08
- Time: 16:33:01 +05:30
- Importance: High
- What It Updated: A separate `Alpha Website Logic Engine` product folder
- What It Fixed: Alpha now has a dedicated browser product for websites, forms, and admin tools instead of only a general-purpose coding studio
- Update Details:
  - added `Alpha Website Logic Engine/engine_server.py` as a standalone website logic server
  - added browser UI files for templates, saved scripts, payload testing, results, and logs
  - added reusable website logic templates such as contact forms, admin approval, inventory guard, and dashboard widgets
  - added local script storage in `Alpha Website Logic Engine/engine_data/saved_scripts`
  - added execution logging in `Alpha Website Logic Engine/engine_data/execution_logs.json`
  - added a public API route at `/api/public/execute` for websites and forms to call saved Alpha scripts
  - added a README and app shell files for the new website logic engine folder
  - updated the project checklist to mark the website logic engine goal as complete

## Update Entry 22

- Date: 2026-04-08
- Time: 17:05:21 +05:30
- Importance: Critical
- What It Updated: A separate `alpha mobile coder studio apk` Android project folder
- What It Fixed: Alpha now has an APK-ready Android app project which embeds the main browser studio layout instead of only a phone-first browser or PWA version
- Update Details:
  - added `alpha mobile coder studio apk/` as a dedicated Android Studio project
  - added Android build files, manifest, theme resources, and a native WebView shell
  - embedded the main Alpha Studio `index.html`, `style.css`, and `studio.js` inside the Android app project
  - embedded Alpha runtime source files, rules, database schema, and package registry inside the app project
  - added `android_mobile_host.py` to start a local Alpha HTTP server inside the app on `127.0.0.1`
  - kept local user accounts, saved projects, package management, run history, and guide routes working through the embedded server
  - added build notes explaining where the generated APK will appear after Android Studio builds the project
  - recorded that a compiled `.apk` could not be generated on this machine because the Android toolchain was not available

## Update Entry 23

- Date: 2026-04-08
- Time: 17:40:08 +05:30
- Importance: High
- What It Updated: A separate `Alpha learner` beginner learning platform
- What It Fixed: Alpha now has a dedicated lesson-based education product for students instead of only development-focused studios
- Update Details:
  - added `Alpha learner/learn_server.py` as a standalone Alpha Learn browser server
  - added guided lesson tracks for foundations, logic, and builder skills
  - added a real Alpha code lab powered by the existing interpreter
  - added progress tracking with completed lessons, badges, and quiz scoring in browser storage
  - added glossary cards, quick wins, checkpoints, and beginner-friendly error explanations
  - added a dedicated responsive learning UI with lesson path, quiz area, glossary, and progress panels
  - added a README, manifest, and service worker files for the Alpha Learn product folder

## Update Entry 24

- Date: 2026-04-08
- Time: 17:55:49 +05:30
- Importance: Medium
- What It Updated: A separate run guide book for moving Alpha to another Windows PC
- What It Fixed: The project now includes a dedicated book explaining what is needed to run all main Alpha folders, Python files, and products after copying the project by pen drive
- Update Details:
  - added `Alpha cod books/Run Alpha On Another PC Guide.md`
  - documented what must be installed on another PC before running Alpha
  - documented passwords, browser requirements, tkinter requirement, and Android build note
  - documented startup commands for Alpha Studio, Alpha Learn, Alpha Kids, Alpha Website Logic Engine, and desktop software
  - documented common problems such as PATH, firewall, LAN access, and removable-drive write issues

## Update Entry 25

- Date: 2026-04-09
- Time: 10:56:58 +05:30
- Importance: High
- What It Updated: Security reporting and business/source-use policy documentation
- What It Fixed: The project now has a separate vulnerability reporting file and a draft policy explaining credit, commercial-use permission, and source-protection expectations
- Update Details:
  - added root `SECURITY.md` for repository security reporting guidance
  - added `Alpha cod books/Commercial Use, Credit, and Source Protection Policy.md`
  - documented required visible credit to `Bluear_cod`
  - documented that business or large-project use should require a paid written commercial license
  - documented that the core Alpha code should not be copied or republished without written permission
  - documented that earlier public open-source releases may still keep earlier granted rights and should be reviewed carefully before relying on stricter future terms

## Update Entry 26

- Date: 2026-04-09
- Time: 10:56:58 +05:30
- Importance: Critical
- What It Updated: The repository license position from MIT/open-source wording to Bluear_cod proprietary / brand-property wording for the current repository state
- What It Fixed: The main license files, visible studio footer text, books, and policy wording now match a proprietary source-available position instead of continuing to say MIT/open source
- Update Details:
  - added root `LICENSE` as `Bluear_cod Proprietary Source-Available License`
  - replaced `Alpha cod books/LICENSE` with the proprietary source-available license text
  - updated `NOTICE` and the books README to match the new license position
  - updated the main studio footer and APK project studio footer away from MIT/open-source wording
  - updated the Alpha language book and source/protection guide to match proprietary wording
  - updated the checklist wording from open-source license to project license
  - kept the warning that earlier public releases may still keep earlier granted rights and should be reviewed carefully

---

## Current High-Value Language Features

Alpha currently includes:
- readable syntax keywords
- safe imports
- database helpers
- file helpers
- package system
- SQL bridge
- Python-expression bridge
- package bridge
- Turtle support
- mobile and desktop studio support
- runtime validation and CSV/date/time helpers

## Recommended Future Update Entry Format

Use this format for the next update:

```text
## Update Entry X

- Date:
- Time:
- Importance:
- What It Updated:
- What It Fixed:
- Update Details:
  - 
  - 
  - 
```
