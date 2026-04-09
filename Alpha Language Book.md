# Alpha Language Book
                                    #cridts#
                                Critor ;Bluaar(alixe)
                           COPRIGTHGT BY ; BLUAAR@ALAXE
                        CONTACK EMILE : aritrad947@gmail.com
                                number ; 8282944062
## 1. What Alpha Is
Alpha is a human-friendly interpreted programming language.
It is designed so people can read code like instructions, while the computer can still run it through the Alpha interpreter.

Alpha gives you:
- readable keywords such as `note`, `set`, `if`, `repeat`, and `function`
- immediate execution without a separate compile step
- database support
- safe module imports
- file helpers
- installable packages
- browser studio support
- mobile access through Alpha Studio

## 2. How Alpha Code Works

Alpha has two main parts:

1. Alpha statements
These are the language keywords such as:
- `note`
- `set`
- `if`
- `otherwise`
- `unless`
- `while`
- `repeat`
- `function`
- `give`
- `use`
- `package`
- `try`
- `catch`
- `finally`
- `with`
- `end`

2. Expressions inside statements
Inside Alpha statements, many values and expressions behave like Python expressions.
That means these kinds of values work naturally:
- numbers like `10` and `3.14`
- strings like `"hello"`
- lists like `[1, 2, 3]`
- dictionaries like `{"name": "Alpha"}`
- booleans like `true` and `false`
- conditions like `score > 10 and ready == true`
- method calls like `text.upper()`

## 3. First Program

```alpha
note "Hello from Alpha!"

set name = "world"

function greet(person)
    note "Hello, " + person + "!"
end

greet(name)
```

Expected output:

```text
Hello from Alpha!
Hello, world!
```

## 4. Comments

Use `#` for comments.

```alpha
# This is a comment
note "Alpha is running"
```

Alpha also supports `$` and `$$` comments.

### One-Line Comment With `$`

```alpha
$ This is a one line Alpha comment
note "Alpha is running"
```

You can also place it after code:

```alpha
note "Hello" $ inline comment
```

### Multi-Line Comment With `$$`

```alpha
$$
This is a multi-line Alpha comment.
It can cover many lines.
$$

note "Code continues here"
```

## 5. Values And Data Types

### Text

```alpha
set title = "Alpha Language"
note title
```

### Numbers

```alpha
set total = 50
set price = 99.5
note total + price
```

### Booleans

Alpha supports:
- `true`
- `false`
- `nothing`
- `null`

```alpha
set is_ready = true
set no_value = nothing
note is_ready
note no_value
```

### Lists

```alpha
set numbers = [1, 2, 3, 4]
note numbers
note numbers[0]
```

### Dictionaries

```alpha
set user = {"name": "ARD", "role": "builder"}
note user
note user["name"]
```

## 6. Printing Output

Use `note` to show output.

```alpha
note "Alpha is running"
note 10 + 20
note {"status": "ok"}
```

## 7. Variables

Use `set` to create or update a variable.

```alpha
set name = "Alpha"
set count = 1
set count = count + 1
note count
```

## 8. Operators

### Math

```alpha
set a = 10 + 5
set b = 10 - 2
set c = 4 * 3
set d = 20 / 5
set e = 2 ** 4
note a
note b
note c
note d
note e
```

### Comparison

```alpha
note 10 > 5
note 10 < 5
note 10 == 10
note 10 != 8
```

### Logic

```alpha
set ready = true
set admin = false

note ready and true
note ready or admin
note not admin
```

## 9. Conditions

### If

```alpha
set total = 20

if total > 10 then
    note "Large"
end
```

### If / Otherwise If / Otherwise

```alpha
set marks = 76

if marks >= 90 then
    note "Grade A"
otherwise if marks >= 75 then
    note "Grade B"
otherwise
    note "Keep learning"
end
```

### Unless

`unless` is the opposite of `if`.

```alpha
set is_ready = false

unless is_ready then
    note "System is not ready"
end
```

## 10. Loops

### Repeat Over A List

```alpha
set items = ["pen", "book", "desk"]

repeat item in items
    note item
end
```

### Repeat With A Numeric Range

```alpha
repeat number from 1 to 5
    note number
end
```

### Repeat With Step

```alpha
repeat number from 2 to 10 step 2
    note number
end
```

### While Loop

```alpha
set count = 0

while count < 3 do
    note count
    set count = count + 1
end
```

### Break And Continue

Use:
- `stop` for break
- `skip` for continue

```alpha
repeat number from 1 to 6
    if number == 2 then
        skip
    end

    if number == 5 then
        stop
    end

    note number
end
```

## 11. Functions

### Function With Arguments

```alpha
function add(a, b)
    give a + b
end

note add(5, 7)
```

### Function Without Arguments

```alpha
function welcome()
    note "Welcome to Alpha"
end

welcome()
```

### Returning Complex Data

```alpha
function build_user(name, role)
    give {"name": name, "role": role}
end

set user = build_user("ARD", "creator")
note user
```

## 11A. Classes And Objects

Use `class` when you want bigger Alpha programs with reusable objects.

### Basic Class

```alpha
class Person
    function __init__(self, name)
        set self.name = name
    end

    function greet(self)
        give "Hello, " + self.name
    end
end

set user = Person("Alpha")
note user.greet()
```

### Class With Inheritance

```alpha
class Student extends Person
    function __init__(self, name, level)
        Person.__init__(self, name)
        set self.level = level
    end

    function describe(self)
        give self.greet() + " from level " + str(self.level)
    end
end
```

You can write class headers in these styles:
- `class Person`
- `class Student extends Person`
- `class Student(Person)`

Useful object helpers available in Alpha now:
- `getattr`
- `setattr`
- `hasattr`
- `isinstance`
- `issubclass`
- `super`

## 12. Error Handling

Use `try`, `catch`, and `finally`.

```alpha
try
    set result = 10 / 0
catch err
    note err
finally
    note "done"
end
```

## 13. Using Safe Modules

Use `use` to import safe modules.

```alpha
use math
note math.sqrt(81)
```

You can also use an alias:

```alpha
use math as m
note m.sqrt(49)
```

Safe modules currently include:
- `collections`
- `csv`
- `datetime`
- `functools`
- `itertools`
- `json`
- `math`
- `pathlib`
- `random`
- `re`
- `statistics`
- `time`
- `turtle`

## 14. Packages

Alpha includes a local package system.

Current packages:
- `collections_plus`
- `text_tools`
- `math_plus`

### Load A Package

```alpha
package text_tools
note slugify("Alpha Language Book")
```

### Load A Package With Alias

```alpha
package text_tools as text_tools_lib
note text_tools_lib.slugify("Alpha Language Book")
```

### Install And Remove Packages From Code

```alpha
note available_packages()
note package_install("text_tools")
note packages()
note package_remove("text_tools")
```

### Text Package Example

```alpha
package text_tools

set sentence = "alpha works on phone and desktop"
note slugify(sentence)
note title_case(sentence)
note word_count(sentence)
```

### Math Package Example

```alpha
package math_plus

note average_of([10, 20, 30])
note clamp_value(150, 0, 100)
note percent_of(25, 40)
```

### Collections Package Example

```alpha
package collections_plus

set data = [1, 1, 2, 3, 3, 4]
note unique_items(data)
note chunk_items(data, 2)
note group_by_key(
    [
        {"team": "A", "name": "Ali"},
        {"team": "A", "name": "Sara"},
        {"team": "B", "name": "Ravi"}
    ],
    "team"
)
```

## 15. Built-In Runtime Helpers

Alpha includes useful helper functions.

### List Helpers

```alpha
set numbers = [1, 2, 3]
push(numbers, 4)
insert_at(numbers, 1, 99)
note numbers
note pop_from(numbers)
note numbers
```

### Text Helpers

```alpha
note join_text(["A", "l", "p", "h", "a"], "")
note split_text("red,green,blue", ",")
note replace_text("alpha language", "alpha", "ALPHA")
note to_text(123)
note to_number("45")
```

### Data Helpers

```alpha
set user = {"name": "ARD", "role": "builder"}
note keys_of(user)
note values_of(user)
note pairs_of(user)
note length(user)
note contains(["a", "b", "c"], "b")
```

### Slice Helper

```alpha
set items = [10, 20, 30, 40, 50]
note slice_of(items, 1, 4, 1)
```

## 16. Database Coding

Alpha includes a built-in SQLite-backed key-value database.

### Store And Read Data

```alpha
store("project", {"name": "Alpha", "version": 1})
set project = fetch("project")
note project
```

### Read With Default Value

```alpha
note fetch("missing_key", {"status": "not found"})
```

### Remove Data

```alpha
store("temp", {"value": 10})
note erase("temp")
```

### List Records

```alpha
note records()
```

### Run History

```alpha
note history(5)
```

## 17. SQL Bridge

The SQL bridge is read-only.

```alpha
note bridge("sql", "SELECT key, value_json FROM key_value_store ORDER BY key")
```

Allowed query styles:
- `SELECT`
- `WITH`
- `PRAGMA`

## 18. Python Expression Bridge

Use this when you want a safe one-line Python expression.

```alpha
note bridge("python_expr", "sum([1, 2, 3, 4])")
note bridge("python_expr", "sorted([9, 1, 5, 2])")
```

## 19. Package Bridge

```alpha
note bridge("packages", "available")
note bridge("packages", "installed")
note bridge("packages", "install text_tools")
note bridge("packages", "remove text_tools")
```

## 20. File Coding

Alpha can work with files safely inside the project workspace.

### Create A Folder

```alpha
note make_folder("notes")
```

### Write And Read A File

```alpha
write_text("notes/hello.txt", "Hello from Alpha")
note read_text("notes/hello.txt")
```

### Append Text

```alpha
write_text("logs/run.txt", "Start\n")
append_text("logs/run.txt", "Next line\n")
note read_text("logs/run.txt")
```

### Check Paths

```alpha
note exists("logs/run.txt")
note path_text("logs/run.txt")
```

### Use A Context Manager

```alpha
with open("notes/sample.txt", "w") as file do
    file.write("Written with Alpha")
end

with open("notes/sample.txt", "r") as file do
    note file.read()
end
```

## 21. JSON Coding

```alpha
set payload = {"name": "Alpha", "version": 1}
set raw = write_json(payload)
note raw
note read_json(raw)
```

## 22. Turtle Graphics

Alpha can also run Turtle graphics.

```alpha
use turtle

set window = turtle.Screen()
window.bgcolor("white")
window.title("Alpha Turtle Animation")
window.tracer(0)

set mover = turtle.Turtle()
mover.shape("circle")
mover.color("blue")
mover.penup()

repeat frame from 1 to 1200
    mover.forward(1)
    if mover.xcor() > 200 or mover.xcor() < -200 then
        mover.right(180)
    end
    window.update()
end

window.mainloop()
```

Important:
- Turtle opens a native desktop window
- run Turtle on a PC
- mobile can edit the code in Alpha Studio, but the Turtle window appears on the computer

## 23. Human-Language Keyword Aliases

Alpha also supports friendly aliases.

Examples:
- `print`, `say`, `bolo` -> `note`
- `let`, `remember`, `rakho` -> `set`
- `agar` -> `if`
- `return`, `wapas` -> `give`
- `load`, `lao` -> `use`
- `plugin` -> `package`

Example:

```alpha
bolo "Hello"
rakho name = "Alpha"
agar true then
    bolo name
end
```

Recommended style:
- use the main Alpha keywords in shared code
- use aliases only when they help your audience

## 24. Full Example Programs

### Example: Hello World

```alpha
note "Hello from Alpha!"
```

### Example: Feature Showcase

```alpha
unless false then
    note "Unless logic is working"
end

repeat number from 1 to 5 step 2
    note number
end

set data = [1, 1, 2, 3, 3, 4]
package collections_plus
note unique_items(data)
note chunk_items(data, 2)
```

### Example: Database Program

```alpha
store("language", {"name": "Alpha", "type": "interpreted"})
set saved = fetch("language")
note saved
note bridge("sql", "SELECT key, value_json FROM key_value_store ORDER BY key")
```

### Example: File Program

```alpha
make_folder("reports")
write_text("reports/summary.txt", "Alpha report")
append_text("reports/summary.txt", "\nDone")
note read_text("reports/summary.txt")
```

### Example: Package Program

```alpha
package text_tools
package math_plus

set words = "alpha is ready for mobile and desktop"
note slugify(words)
note title_case(words)
note word_count(words)
note percent_of(25, 80)
```

## 25. How To Run Alpha Code

### Run From Command Line

```powershell
python "Maine File/alpha.py" "Examples/hello.alpha"
```

### Run A Sample

```powershell
python "Maine File/alpha.py" --sample
```

### Show Translated Python

```powershell
python "Maine File/alpha.py" "Examples/hello.alpha" --show-python
```

## 26. How To Run Alpha Studio

### Desktop

```powershell
python "Maine File/maine.py"
```

Open:

```text
http://127.0.0.1:8080
```

### Mobile And PC Together

```powershell
python "Maine File/maine.py" --share-lan
```

Then:
1. Keep the server running.
2. Connect phone and PC to the same trusted Wi-Fi.
3. Open the printed `192.168...` address on your phone.

### User Accounts And Saved Projects

Alpha Studio now supports local browser accounts with different passwords for different users.

What you can do:
- create a user with your own password
- sign in with that user
- change the password later
- save Alpha projects to your own user folder
- load saved projects back into the editor

Saved data is stored in:
- `alpha_user_data/users/<username>/profile.json`
- `alpha_user_data/users/<username>/projects/*.alpha`

Basic workflow:
1. Open Alpha Studio in the browser.
2. Create a user in the `Accounts` area.
3. Enter a project name.
4. Click `Save Project`.
5. Open the `Saved Projects` panel to load it again later.

## 27. Writing Style Tips

Good Alpha code should be:
- readable
- short when possible
- clearly named
- safely structured with `end`
- broken into functions for reuse

Good example:

```alpha
function calculate_total(price, tax)
    give price + tax
end

set total = calculate_total(100, 18)
note total
```

## 28. Common Mistakes

### Missing `then`

Wrong:

```alpha
if true
    note "Hi"
end
```

Correct:

```alpha
if true then
    note "Hi"
end
```

### Missing `do`

Wrong:

```alpha
while true
    note "Loop"
end
```

Correct:

```alpha
while true do
    note "Loop"
    stop
end
```

### Missing `end`

Wrong:

```alpha
function hello()
    note "Hello"
```

Correct:

```alpha
function hello()
    note "Hello"
end
```

## 29. Where To Extend Alpha

To grow the language:
- edit `Rouls File/rulls.py` for keywords, safe modules, rules, and samples
- edit `Maine File/alpha.py` for interpreter behavior, helpers, bridges, and packages
- edit `Packages/registry.json` for package catalog data

## 30. Proprietary Use, Private Code, Encryption, and Bluear_cod Ownership

Alpha is now described in this project as proprietary / brand property of `Bluear_cod`.

Important truth:
- learning and evaluation use may be allowed under the project policy
- business or large-scale use should require written paid permission
- browser code cannot be truly hidden because the browser must receive it
- Python code can stay private only if you keep it on your own server or machine and do not distribute it
- obfuscation can make code harder to read, but it does not create perfect protection
- company branding such as `Bluear_cod` does not by itself create patent rights
- actual patent ownership depends on inventorship, assignment, filing, and patentability rules
- older public releases may still need separate legal review if they were distributed under earlier different terms

Best rule:
- keep sensitive business logic on the server side if you want it private
- use written commercial terms for paid, client, or company use

Read these project files too:
- `LICENSE`
- `NOTICE`
- `Commercial Use, Credit, and Source Protection Policy.md`
- `Alpha Source, Open Source, and Protection Guide.md`
- `Bluear_cod Patent Readiness Pack.md`

## 31. Final Summary

You can now write all major Alpha code styles with this book:
- output code
- variable code
- condition code
- loop code
- function code
- class and object code
- error-handling code
- module import code
- package code
- database code
- SQL bridge code
- Python-expression bridge code
- file code
- JSON code
- Turtle graphics code
- mobile and desktop studio workflow
- browser user accounts and project save/load workflow
- licensing and source-protection workflow

This book is your main guide for writing Alpha code from beginner level to advanced project level.


 COPRIGTHGT BY ; BLUAAR@ALAXE
 CONTACK EMILE : aritrad947@gmail.com
number ; 8282944062
