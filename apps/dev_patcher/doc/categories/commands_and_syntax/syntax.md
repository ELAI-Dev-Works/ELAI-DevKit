# DevPatcher Documentation

This document describes all available commands, their arguments, and syntax.

## Variables

- `@ROOT`: This variable represents the path to the **selected project folder**. It is used for all operations related to the target project.

**Note(Important):** @ROOT var, mandatory for ALL file managing and editing commands.

- `@APP-ROOT`: This variable represents the path to the **ELAI-DevKit/DevPatcher application folder itself**. It is used only for self-update operations.

- `---end---` : Mandatory string for completing a command. Used in all commands.

- `---old---` : Mandatory string for replacing, inserting, and deleting content from a file. Used only in the EDIT command.

- `---new---` : Mandatory string for replacing (-replace) and inserting (-insert) content in a file. Used only in the EDIT command.

- `{content}` : A placeholder for inserting code at a specific location in a file, indicated in the `---old---` string. It must be present inside the `---old---` string to correctly apply content insertion without errors. It is accompanied by two other markers `{code_start}` and `{code_end}`. More details are available in the EDIT command help.


## Comments

DevPatcher supports comments that are completely ignored by the parser during execution.

- `<-@ Text @->` : **Single-line comment**. Must be placed on a separate line. Used for brief notes.
- `#@#` : **Multi-line comment marker**. Acts as a toggle. Place `#@#` on a line by itself to start a comment block, and another `#@#` on a separate line to end it.

### Examples

```
<-@ This is a comment describing the next step @->
<@|TEST -print
This line is visible.
#@#
This block is commented out.
It will be ignored.
#@#
This line is visible again.
---end---
```

---

## Command Syntax

All commands have strict syntax; failure to observe it will lead to patcher errors.

Each command must be written according to its syntax. You can learn more about the syntax of each command by reading the individual help for each command listed at the bottom of this documentation.

## Command Execution Order

Commands are executed in a specific order/priority:

1 - TEST

2 - PROJECT

3 - GIT

4 - DOWNLOAD

5 - MANAGE

6 - EDIT

7 - REFACTOR


This is necessary to prevent conflicts between commands.

## "Raw Execution" Mode `{!RUN}`

Sometimes it is necessary for the command content to be **completely ignored** by the parser. This is especially important when creating documentation files (.md) or simple text files (.txt), where constructions similar to commands may occur but should not be executed.

For this, a special wrapper `{!RUN}` at the beginning and `{!END}` at the end is used.

### Syntax

```
{!RUN}<@|MANAGE -create my_doc.txt
This content will be completely ignored by the parser.
Even if there is <@|TEST -print here, it will not be executed.
---end---{!END}
```

### Usage Rules

- The `{!RUN}` tag must be placed immediately before `<@|`.
- The `{!END}` tag must be placed immediately after `---end---`.
- All text between `{!RUN}<@|...` and `---end---{!END}` is passed to the command as is, without any analysis.

---

`---scope---`: **(Advanced)** The beginning of a block within which the search for `---old---` will be performed. Increases search accuracy if there are several identical `---old---` blocks in the file.

### Advanced and Experimental Features

In the PatcherApp graphical interface, the "Experimental Features" block is available. It activates more advanced algorithms for the `EDIT` command.

- **Fuzzy Matching (Advanced Function)**: If this option is enabled, the patcher will not look for an exact match for the `---old---` block, but the **most similar** one (with a similarity threshold >85%). This allows the patch to be successfully applied even if minor changes were made in the source code (e.g., a variable was renamed). This function is considered stable.

- **Scope Matching (Advanced Function)**: This option activates the use of the new `---scope---` block. The patcher first finds this "scope" block (e.g., a function or class definition), and then searches for `---old---` **only inside it**. This radically solves the ambiguity problem. Requires active *Fuzzy Matching*.

- **Precise Patching (with line numbers, Experimental)**: This option allows including line numbers in the command body, right-aligned and separated by the `|` symbol. Ideal for one-off (one edit for one file per patch) large edits, as they require precise context and line numbers in the code. When applying the patch, these line numbers are automatically stripped.

#### Example of using `---scope---`
```
<@|EDIT -v1 -replace @ROOT/main.py
---scope---
def my_target_function(param1, param2):
    # Function code...
---old---
    # Fragment to be replaced
    # It will be searched only inside my_target_function
    version = "1.0"
---new---
    version = "2.0" # Updated version
---end---
```

#### Example of using line numbers for the Precise Patching function
```
<@|EDIT -v2 -replace @ROOT/config.py
---old---
 95| class ProductionConfig(BaseConfig):
 96|     DEBUG = False
 97|     SECRET_KEY = os.getenv("PROD_SECRET")
---new---
 95| class ProductionConfig(BaseConfig):
 96|     DEBUG = False
 97|     SECRET_KEY = os.getenv("PROD_SECRET_KEY_UPDATED")
---end---
```
With the "Precise Patching" option enabled, this patch will be processed as if it were written without the `95|`, `96|`, and `97|` prefixes.

---

## `TEST` Command

The simplest command, designed for debugging and outputting information to the log.

### Arguments
- `-print`: Required. Everything in the command body will be output to the log.

- `-search`: Searches for files and folders by keywords.
- `-ignore`: Modifier for `-search`. Allows excluding folders/files from the search.


### Variables


#### Printing a message (`-print`)
Prints the content of the command body to the log. Useful for debugging or user notifications.

```
<@|TEST -print
This message will appear in the log.
Project path: @ROOT
---end---
```

#### Searching for files (`-search`)
Searches for files and folders containing specific keywords in their names.

**Modifiers:**
- `-ignore <pattern1, pattern2...>`: Excludes items matching the patterns.

#### Example 1: Search by Name
```
<-@ Find all files containing 'api' or 'test', ignoring '.venv' @->
<@|TEST -search <api|test> -ignore <.venv>
---end---
```

#### Example 2: Search by Extension
```
<-@ Find all Python and JavaScript files @->
<@|TEST -search <.py|.js>
---end---
```

---

## PROJECT Command

Creates the basic structure and files for configuring a new project. This command helps to quickly deploy an environment with dependency management and a full project structure in a single step.

### Arguments
- `-setup`: The main command for project initialization.

- `-run <startup_file>`: **(Mandatory)** Specifies the entry point for the application.

- `-requi <dependencies>`: **(Mandatory)** Specifies dependencies to install, separated by `|`. If dependencies are not needed, use `<None>`.

- `-name <Project Name>`: (Optional) Sets the project name in console headers and file templates.

- `-tree`: (Optional) Indicates that the command body contains a tree structure block.

- `-python`: Activates Python mode. Creates launch files for `uv` and `pip`.

- `-web`: Activates Web/HTML5 mode. Creates `index.html` and a local server script.

- `-nodejs`: Activates Web/Server mode. Creates `package.json` and `run(nodejs)` scripts.

- `-npm <command>`: **(Optional, only for NodeJS)** Configures launch commands and `package.json` scripts.

- `-all_os`: Generates launch scripts for both Windows (`.bat`) and Linux/Mac (`.sh`). This is the default if no platform flag is specified.

- `-win_os`: Generates only Windows (`.bat`) scripts.

- `-linux_os`: Generates only Linux (`.sh`) scripts.

- `-mac_os`: Generates only macOS (`.sh`) scripts.

- `-server <Type>`: (Optional, for `-web`) Creates a local server script. Values: `<Python>` or `<NodeJs>`.


### Variables
- `---structure---`: (Optional) Describes the directory tree structure (`/`) and empty files.
- `---project---`: (Optional) Defines the content of files created. **Note**: Required for -tree and ---structure--- if files in the specified structure are to be populated, as using the MANAGE -create command on existing files will fail, so use ---project--- or the MANAGE -write command to overwrite files created by -tree and ---structure---.
- `---file_end---`: Marker ending the content block for a single file.


#### Setup (`-setup`)
The main command for project initialization.

**Syntax:**
```
<@|PROJECT -setup [-all_os|-win_os|-linux_os] -<mode> -run <file> -requi <dependencies> [-npm <{command}>] [-tree] [-name <(Project Name)>]
---structure---
[...tree structure...]
---project---
---end---
```

**Command Body:**
1.  `---structure---`: (Optional) Describes the directory tree structure (`/`) and empty files.
2.  `---project---`: (Optional) Defines the content of files created. Separated by `<###| path/to/file>`.

### Usage Examples

#### 1. Basic Python Project (Windows)
Creates a simple Python project with a virtual environment and a run script for Windows.

```
<@|PROJECT -setup -win_os -python -run <main.py> -requi <requests|colorama> -name <MyTool>
---project---
<###| @ROOT/main.py
import requests
print("Hello World")
---file_end---
---end---
```

#### 2. Cross-Platform Python Project with Structure
Creates a project structure for Linux, Mac, and Windows, generating appropriate `.sh` and `.bat` scripts.

```
<@|PROJECT -setup -all_os -python -tree -run <app.py> -requi <numpy> -name <(Data App)>
---structure---
@ROOT/
├── core/
│   └── processing.py
├── data/
└── app.py
---project---
<###| @ROOT/app.py
import core.processing
print("App Started")
---file_end---
---end---
```

#### 3. NodeJS Project (Simple)
Creates a `package.json` with Express and a startup script.

```
<@|PROJECT -setup -all_os -nodejs -run <server.js> -requi <express> -name <WebServer>
---project---
<###| @ROOT/server.js
console.log("Server running...");
---file_end---
---end---
```

#### 4. NodeJS Advanced (Electron)
Configures specific NPM scripts and a custom run command for the generated `.bat/.sh` file.

```
<@|PROJECT -setup -win_os -nodejs -run <main.js> -requi <electron> -name <(My Electron App)>
-npm <run:{npm start}|scripts/start:{electron .}|scripts/build:{electron-builder}>
---project---
<###| @ROOT/main.js
const { app, BrowserWindow } = require('electron')
// ... app code ...
---file_end---
---end---
```

#### 5. HTML5 Web project
Setting up an HTML5 project using a local Python server and phaser engine lib.

```
<@|PROJECT -setup -win_os -web -server <Python> -run <index.html> -requi <src:https://cdn.jsdelivr.net/npm/phaser/dist/phaser.min.js> -name <(My Phaser Game)>
```


#### Startup File (`-run`)
**Mandatory.** Specifies the entry point for the application.

*   **For Python:** Specifies the script to run.
    *   Example: `-run <main.py>` -> Executes `python main.py`.
    *   Example: `-run <src/app.py>` -> Executes `python src/app.py`.

*   **For NodeJS:** Specifies the main entry file for `package.json`.
    *   Example: `-run <server.js>` -> Sets `"main": "server.js"` and default start command to `node server.js`.
    *   If combined with `-npm`, this argument only sets the `"main"` field, while the execution command is determined by `-npm`.

#### Dependencies (`-requi`)
**Mandatory.** Specifies dependencies to install, separated by `|`.
If dependencies are not needed, use `<None>`.

*   Example: `<pygame|requests>` (for Python)
*   Example: `<react|typescript>` (for NodeJS)
*   Example: `<src:https://cdn.jsdelivr.net/npm/phaser/dist/phaser.min.js>` (for HTML5 web project)

#### Project Name (`-name`)
(Optional) Sets the project name in console headers and file templates.

*   **Without spaces:** `<MyProject>`
*   **With spaces:** `<(My Project Name)>` (Must be wrapped in parentheses inside the brackets).

#### Tree Structure (`-tree`)
(Optional) Indicates that the command body contains a tree structure block.
Requires the presence of a `---structure---` block in the command body.

### Example

```
<@|PROJECT -setup -python -run <main.py> -requi <None> -tree
---structure---
@ROOT/
├── main.py
├── config/
│   ├── settings.json
│   └── secrets.yaml
├── src/
│   ├── utils/
│   │   └── helper.py
│   └── api/
└── tests/
---end---
```
**Note:** Files listed in the tree structure (like `main.py` or `helper.py`) will be created as empty files unless their content is defined in a separate `---project---` block.

**Note 2(Important):** If you use -tree to create the folder and file structure, do not use the MANAGE -create command, as the patcher will return an error. To change the contents of files, use either the ---project--- block (recommended for the PROJECT command), or the MANAGE -write command to overwrite empty files created via -tree.

#### Python Mode (`-python`)
Activates Python mode. Creates launch files:
*   `setup_run(uv)`: Uses `uv` for fast setup.
*   `run(pip)`: Uses standard `pip`.

#### Web/HTML5 Mode (`-web`)
Activates Web/HTML5 mode. Creates a basic `index.html` and optionally a local server script to bypass CORS.

*   **Dependencies:** Uses `-requi` to inject scripts.
    *   Format: `<src:URL|src:URL>`
    *   Example: `-requi <src:https://cdn.jsdelivr.net/npm/phaser/dist/phaser.min.js>`
*   **Server:** Uses `-server` to generate a `server.bat/sh`.

#### NodeJS Mode (`-nodejs`)
Activates Web/Server mode. Creates `package.json` and `run(nodejs)` scripts.

#### NPM Commands (`-npm`)
(Optional, only for NodeJS) Configures launch commands and `package.json` scripts.

**Formats:**
1.  **Simple:** `-npm <{command}>` (e.g. `-npm <{npm run dev}>`).
2.  **Advanced:** `-npm <key:{value}|key:{value}>`.
    *   `run:{...}`: Command for the `.bat` file.
    *   `scripts/name:{...}`: Entry in `package.json` scripts section.
    *   Example: `-npm <run:{npm start}|scripts/start:{electron .}>`.

### Examples

#### Simple Mode
Adds `npm run dev` to the launch script and registers it as the start script in package.json.
```
-npm <{npm run dev}>
```

#### Advanced Mode (Electron Example)
1.  Sets the launch script (`run.bat`) to execute `npm start`.
2.  Adds `"start": "electron ."` to `package.json`.
3.  Adds `"dist": "electron-builder"` to `package.json`.

```
-npm <run:{npm start}|scripts/start:{electron .}|scripts/dist:{electron-builder}>
```

#### Advanced Mode (Vite Example)
1.  Sets the launch script to `npm run dev`.
2.  Adds `"dev": "vite"` to `package.json`.
3.  Adds `"build": "vite build"` to `package.json`.

```
-npm <run:{npm run dev}|scripts/dev:{vite}|scripts/build:{vite build}>
```

#### Platform: All (`-all_os`)
Generates launch scripts for both Windows (`.bat`) and Linux/Mac (`.sh`). This is the default if no platform flag is specified.

#### Platform: Windows (`-win_os`)
Generates only Windows (`.bat`) scripts.

#### Platform: Linux (`-linux_os`)
Generates only Linux (`.sh`) scripts.

#### Platform: macOS (`-mac_os`)
Generates only macOS (`.sh`) scripts.

#### Local Server (`-server`)
(Optional, only for `-web` mode) Generates a script to run a simple local HTTP server. This is useful for testing HTML5 projects that require bypassing CORS restrictions.

*   **Values:**
    *   `<Python>`: Uses `python -m http.server`.
    *   `<NodeJs>`: Creates a minimal `server.js` and runs it with `node`.

---

## `GIT` Command

Executes Git version control system commands. Requires `git` to be installed on the system and available in the `PATH`.

### Arguments
The `GIT` command accepts standard Git command-line arguments.

- `init`: Initializes a new repository in the `@ROOT` folder.
- `clone <URL> .`: Clones a repository into the `@ROOT` folder. **The dot at the end is required to clone into the existing project folder.**
- `pull`: Pulls changes from a remote repository.
- `add`, `commit`, `push`: Other standard commands.

### Examples

#### Cloning a repository into the current project folder

```
<@|GIT clone "https://github.com/some/repository.git" .
---end---
```

#### Initializing a repository

```
<@|GIT init
---end---
```

#### Adding all files and creating a commit

```
<@|GIT add .
---end---

<@|GIT commit -m "Initial commit"
---end---
```


---

## `DOWNLOAD` Command

Downloads a file from the internet and saves it in the project.

### Arguments
- `URL`: First argument. Direct link to the file to download.
- `Destination`: Second argument. The folder within the project where the file will be saved. The filename is required.

### Examples

#### Basic Download
```
<-@ Download the `.png` icon to the `assets/icons` folder @->
<@|DOWNLOAD https://site.com/icon.png @ROOT/assets/icons/icon.png
---end---
```

#### Download with Rename
```
<-@ Download a file and save it with a specific name @->
<@|DOWNLOAD https://site.com/logo_v2_final.png @ROOT/assets/logo.png
---end---
```


---

## The `MANAGE` Command

A powerful command for managing files and folders in the project.

### Arguments
- `-create`: Creates a file or a folder.

- `-write`: Overwrites an existing file with new content.

- `-move`: Moves a file or a folder.

- `-copy`: Copies a file or a folder.

- `-rename`: Renames a file or a folder.

- `-delete`: Deletes a file or a folder.


### Variables



#### Creating files and folders (`-create`)
Creates a new file with content, or a new directory.

**Modifiers:**
- `-dir`: Use this flag to create a directory instead of a file.

```
<-@ Create the `src` folder in the project root @->
<@|MANAGE -create -dir @ROOT/src
---end---

<-@ Create the `config.ini` file with content @->
<@|MANAGE -create @ROOT/config.ini
[Settings]
user = admin
---end---
```

#### Creating Documentation

```
<-@ Create a README file @->
<@|MANAGE -create @ROOT/README.md
# My Project
Welcome to my project.
## Installation
Run `setup.bat`.
---end---
```

#### Overwriting a file (`-write`)
Finds an existing file and completely overwrites its content. If the file does not exist, the command will fail.

```
<-@ Find the `config.ini` file and completely overwrite its content @->
<@|MANAGE -write @ROOT/config.ini
[New Settings]
mode = production
---end---
```


#### Moving (`-move`)
Moves a file or folder to a new location. Can be used to rename if the destination is in the same directory.

**Syntax:** `MANAGE -move [-dir] <source> to <destination>`

```
<-@ Move a file and rename it @->
<@|MANAGE -move @ROOT/main.py to @ROOT/src/app.py
---end---

<-@ Move the `utils` folder into the `src` folder @->
<@|MANAGE -move -dir @ROOT/utils to @ROOT/src
---end---
```

#### Renaming via Move
```
<-@ Move and rename a file simultaneously @->
<@|MANAGE -move @ROOT/styles/old_style.css to @ROOT/styles/main.css
---end---
```
You have that option, but it's more convenient to use the -rename argument in such scenarios.


#### Copying (`-copy`)
Copies a file or folder to a new location.

**Syntax:** `MANAGE -copy [-dir] <source> to <destination>`

```
<-@ Copy the configuration file to backup @->
<@|MANAGE -copy @ROOT/config.ini to @ROOT/config.bak
---end---
```


#### Renaming (`-rename`)
Renames a file or folder in place.

**Syntax:** `MANAGE -rename [-dir] <old_name> as <new_name>`

```
<-@ Rename a file @->
<@|MANAGE -rename @ROOT/old_name.txt as @ROOT/new_name.txt
---end---

<-@ Rename a folder @->
<@|MANAGE -rename -dir @ROOT/docs as @ROOT/documentation
---end---
```


#### Deletion (`-delete`)
Deletes a file or an entire folder.

**Modifiers:**
- `-dir`: Indicates that the target is a directory.

```
<-@ Delete a specific file @->
<@|MANAGE -delete @ROOT/temp_file.tmp
---end---

<-@ Delete an entire folder with all content @->
<@|MANAGE -delete -dir @ROOT/build
---end---
```


---

## The `EDIT` Command

Command for intelligent editing of text file contents. It supports advanced pattern matching and indentation preservation.

### Matching Strategies (Modifiers)

DevPatcher offers two distinct algorithms for finding and applying code changes. You can specify these flags after the command (e.g., `EDIT -v2 -replace ...`). Selecting an algorithm is **mandatory**.

*   **`-v1` - Normalization Strategy**:
    *   Ignores absolute indentation. It "flattens" both the search pattern and the target file content to find a match based on code structure.
    *   **Best for:** Standard edits where you know the code structure but want to be flexible about nesting levels.
    *   **Algorithm problems**: You need to know the indentation rules thoroughly in order to avoid making mistakes when replacing and inserting.

*   **`-v2` - Delta Strategy**:
    *   Calculates the **relative indentation difference** (delta) between your patch's `---old---` block and the actual code in the file.
    *   Applies this delta to the `---new---` block.
    *   **Best for:** Inserting or replacing code when you are unsure of the absolute indentation (e.g., code might be wrapped in a `class` or `if` block you didn't account for), but the *relative* structure is correct.
    *   **Algorithm problems**: Remember to use relative indents and follow the replace and insert rules.

### Arguments
- `-replace`: Finds a code block (`---old---`) and replaces it with a new one (`---new---`).

- `-insert`: Inserts a code block (`---new---`) at a specific location inside `---old---`.

- `-remove`: Finds and removes a code block (`---old---`).


### Variables
- `---old---`: The beginning of the block to be found/modified.
- `---new---`: The beginning of the block with the new content.

- `{code_start}`, `{content}`, `{code_end}`: Marker system for the `-insert` command. These markers are strictly required and must be present in the ---old--- block whenever the EDIT -insert command is used.
- `{content}`: The location where the `---new---` block will be inserted.
- `{code_start}` / `{code_end}`: Controls the addition of empty lines around the inserted code.

- `---old---`: The beginning of the block to be found/removed.




### Replacement (`-replace`)

Finds a specific block of code defined in `---old---` and replaces it with the content of `---new---`.

#### 1. Replacement with Normalization (`-v1 -replace`)

### Visual Guide: How Indentation Works with Normalization algorithm?

The most important aspect of `EDIT` is that **it preserves the relative indentation** of the new code block based on where the old block was found.

**Scenario:** We want to replace logic inside a function.

**1. The "Golden Rule" of Anchoring**
To ensure the patcher calculates the correct indentation, your `---old---` block should start with a line that has the *indentation level you want to use as a base*.

**Target File (`script.py`):**

```python
def calculate():
    # ... some code ...
    x = 10          <-- Target Block (Indented 4 spaces)
    y = 20
```

**The Patch:**

```
<@|EDIT -v1 -replace script.py
---old---
    x = 10
    y = 20
---new---
    x = 100
    y = 200
    z = 300
---end---
```

**Result:**

    The patcher sees that `x = 10` is indented by **4 spaces** in the real file. It then applies those 4 spaces to *every line* in `---new---`.

```python
def calculate():
    # ... some code ...
    x = 100         <-- Automatically indented
    y = 200         <-- Automatically indented
    z = 300         <-- Automatically indented
```

**2. Fixing Broken Indentation**

If the code in the file is *wrongly* indented, and you want to fix it, **do not** start `---old---` with the broken line. Start with a parent line (like `def` or `class`) that is correct.

**Bad File:**

```python
def test():
  print("Wrong indent")  <-- 2 spaces, should be 4
```

**Correct Patch:**

```
<@|EDIT -v1 -replace script.py
---old---
def test():
  print("Wrong indent")
---new---
def test():
    print("Fixed indent")
---end---
```
*Why?* Because `def test():` has 0 indentation. The patcher uses 0 as the base, so the 4 spaces you explicitly wrote in `---new---` are preserved exactly as is.

### Common Mistakes (Anti-Patterns)

It is crucial to choose the correct "Anchor" (the first line of `---old---`) to avoid indentation disasters.

#### The Anchor Trap (`-v1 -replace`)
**Mistake:** Starting the `---old---` block with a line that is *deeper* than the rest of the block you are replacing.

**Target File:**
```python
class App:
    def run(self):
        print("Running")  <-- Indented 8 spaces
    def stop(self):       <-- Indented 4 spaces
        pass
```

**Bad Patch:**
You want to replace `print` and `def stop`. You start `---old---` with the print statement.

```
<@|EDIT -v1 -replace app.py
---old---
        print("Running")
    def stop(self):
        pass
---new---
        print("Running v2")
    def shutdown(self):
        pass
---end---
```

**What Happens:**
1. DevPatcher sees `print("Running")` has **8 spaces** in the file.
2. It sets Base Indentation = 8.
3. It adds 8 spaces to *every line* in `---new---`.

**Result (Broken Code):**
```python
class App:
    def run(self):
        print("Running v2")
        def shutdown(self):  <-- ERROR! Indented 8 spaces, nested inside run()!
            pass
```

**Fix:** Start `---old---` with `def run(self):` (4 spaces) or include context above it.

### Examples

#### Example 1: Simple Variable Replacement
```
<-@ Find the string `version = "1.0"` and replace it @->
<@|EDIT -v1 -replace @ROOT/setup.py
---old---
version = "1.0"
---new---
version = "1.1"
---end---
```

#### Example 2: Replacing Code Logic
```
<-@ Fix a logic error in a function @->
<@|EDIT -v1 -replace @ROOT/core/math_utils.py
---old---
def add(a, b):
    # Old incorrect logic
    return a - b
---new---
def add(a, b):
    # Fixed logic
    return a + b
---end---
```

#### Example 3: Modifying Configuration
```
<-@ Update settings in an INI file @->
<@|EDIT -v1 -replace @ROOT/config.ini
---old---
debug = true
log_level = info
---new---
debug = false
log_level = error
---end---
```

#### 2. Replacement with Delta Strategy (`-v2 -replace`)

Unlike the default V1 algorithm which flattens indentation to compare structure, **V2 (Delta)** calculates the *relative indentation difference* between your patch and the actual file.

**When to use:**
*   When you don't know the absolute indentation of the target code (e.g., user might have wrapped code in a `try/except` block or a class you didn't anticipate).
*   When you want to preserve specific relative indentation in the new block.

**How it works:**
1.  DevPatcher finds the `---old---` block match.
2.  It calculates `Delta = File_Indent - Patch_Indent` based on the first non-empty line.
3.  It adds this `Delta` to every line in `---new---`.

### Visual Guide: V2 Delta Strategy

**Scenario:** Replacing a variable inside a nested structure where absolute depth is unknown or variable.

**Target File:**

```python
class Config:
    def load(self):
        if True:
            # File uses 12 spaces here
            timeout = 10
            retries = 3
```

**The Patch:**
Notice that the patch uses 0 indentation.

```
<@|EDIT -v2 -replace config.py
---old---
timeout = 10
retries = 3
---new---
timeout = 30
retries = 5
---end---
```

**Calculation:**
*   File Indent (`timeout = ...`): 12 spaces.
*   Patch Indent (`timeout = ...`): 0 spaces.
*   **Delta:** 12 - 0 = +12 spaces.

**Result:**
The patcher applies the +12 delta to the new lines.

```python
class Config:
    def load(self):
        if True:
            timeout = 30            <-- Automatically indented to 12 spaces
            retries = 5             <-- Automatically indented to 12 spaces
```

### Common Mistakes (Anti-Patterns)

#### The Delta Trap (`-v2 -replace`)
**Mistake:** Providing a patch where the relative indentation in `---old---` doesn't match the relative indentation in the file, causing a wrong Delta calculation.

**Target File:**
```python
if valid:
    x = 1  # File has 4 spaces relative to 'if'
```

**Bad Patch:**
You write the patch flat, without representing the relative structure.

```
<@|EDIT -v2 -replace script.py
---old---
if valid:
x = 1      <-- Patch has 0 spaces relative to 'if'
---new---
if valid:
y = 2
---end---
```

**Calculation:**
*   File Difference: 4 spaces.
*   Patch Difference: 0 spaces.
*   **Delta:** +4 spaces.

**Result (Unexpected Shift):**
The patcher adds +4 spaces to the *entire* new block relative to where it found the match. The `if valid:` line itself might get shifted if the anchor logic isn't perfectly aligned.

### Examples

#### Example 1: Modifying a Nested Dictionary
The V2 strategy is perfect for data structures where indentation is strictly required but hard to count manually.

**Target File:**
```python
config = {
    "app": {
        "window": {
            "width": 800,
            "height": 600,
        }
    }
}
```

**The Patch:**
Note that the patch uses 0 indentation. The Delta will be calculated from `"width"`.

```
<@|EDIT -v2 -replace settings.py
---old---
"width": 800,
"height": 600,
---new---
"width": 1920,
"height": 1080,
"fullscreen": True,
---end---
```

**Result:**
The new lines will automatically match the indentation of the `window` dictionary (e.g., 12 spaces), keeping the file valid.

### Insertion (`-insert`)

Inserts a code block (`---new---`) at a specific location inside `---old---`.

**Visualizing Markers:**

| Marker Type | Syntax | Behavior |
| :--- | :--- | :--- |
| **Inline** | `{code_start|content|code_end}` | Inserts code tightly, **no extra empty lines**. Perfect for imports. |
| **Multiline** | `{code_start}``{content}``{code_end}` | Adds **empty lines** above and below the inserted code. Perfect for functions/classes. |

**Important Note:** These markers are strictly required and must be present in the ---old--- block whenever the EDIT -insert command is used.

#### 1. Insertion with Normalization (`-v1 -insert`)

### Visual Guide: How Insertion Works with Normalization algorithm?

The `EDIT -insert` command allows you to inject code *between* lines without replacing them. It uses special **markers** to tell the patcher exactly where the new code should go.

**The Logic:**
1.  The patcher finds the `---old---` block in your file.
2.  It looks for the `{content}` marker.
3.  It calculates indentation from the line immediately *above* the marker.
4.  It inserts `---new---` at that position, applying the calculated indentation.

**Note: In the ---new--- block you only need to specify relative indents, without the global insert indent, it is taken from the ---old--- block automatically.**

### Visual Examples

#### Scenario A: Adding an Import (Inline Marker)

**Target File:**

```python
import os
import sys  <-- We want to insert between these
```

**The Patch:**

```
<@|EDIT -insert main.py
---old---
import os
{code_start|content|code_end}
import sys
---new---
import json
---end---
```

**Result:**

```python
import os
import json  <-- Inserted here (tight)
import sys
```

#### Scenario B: Adding a Method to a Class (Multiline Marker)

**Target File:**

```python
class Game:
    def start(self):
        pass
    # <--- We want to insert here, with spacing
    def end(self):
        pass
```

**The Patch:**

```
<@|EDIT -insert game.py
---old---
    def start(self):
        pass
{code_start}
{content}
{code_end}
    def end(self):
---new---
def pause(self):
    print("Paused")
---end---
```

**Result:**

The patcher detects the 4-space indent of `def start...` and applies it to `def pause...`. It also adds blank lines because we used the multiline marker.

```python
class Game:
    def start(self):
        pass

    def pause(self):      <-- Inserted with correct indent + spacing
        print("Paused")

    def end(self):
        pass
```

### Common Mistakes (Anti-Patterns)

#### 1. The Nesting Trap (`-v1 -insert`)
**Mistake:** Inserting a new sibling method, but using the *content* of the previous method as the anchor.

**Target File:**
```python
class User:
    def get_name(self):
        return self.name  <-- Indented 8 spaces
    # We want to insert 'get_age' here (4 spaces)
```

**Bad Patch:**
```
<@|EDIT -insert user.py
---old---
        return self.name
{code_start}
{content}
{code_end}
---new---
    def get_age(self):
        return self.age
---end---
```

**What Happens:**
DevPatcher calculates indentation from `return self.name` (8 spaces). It applies 8 spaces to your new function.

**Result (Broken Code):**
```python
class User:
    def get_name(self):
        return self.name
        def get_age(self):  <-- ERROR! Nested inside get_name
            return self.age
```

**Fix:** Use `def get_name(self):` as the anchor context, or ensure `---old---` includes the end of the previous scope.

### Examples

#### Example 1: Single-line insertion (Imports)
```
<@|EDIT -insert @ROOT/main.py
---old---
import os
{code_start|content|code_end}
import pygame
---new---
import sys
---end---
```

#### Example 2: Inserting a Method into a Class
```
<-@ Insert a new method between existing ones, inheriting indentation @->
<@|EDIT -insert @ROOT/game.py
---old---
    def start(self):
        print("Game Started")

{code_start}
{content}
{code_end}

    def stop(self):
---new---
# This will be inserted with the correct 4-space indent
def pause(self):
    self.paused = True
    print("Game Paused")
---end---
```

#### 2. Insertion with Delta Strategy (`-v2 -insert`)

The V2 strategy is particularly powerful for insertions because it calculates the indentation context dynamically based on the lines *surrounding* the insertion point.

**How it works:**
1.  DevPatcher finds the lines specified before or after the `{content}` marker.
2.  It calculates `Delta` based on the difference between your patch's indentation and the actual file's indentation for those context lines.
3.  It applies this `Delta` to the inserted `---new---` block.

**Scenario:** Inserting code into a deeply nested structure without knowing the exact depth.

**Target File:**
```python
    # Unknown indentation level
    if valid:
        start_process()
        # <--- Insertion point
        end_process()
```

**The Patch:**
```
<@|EDIT -v2 -insert script.py
---old---
start_process()
{code_start|content|code_end}
end_process()
---new---
log_status()
---end---
```

**Result:**
Even if the file uses 4, 8, or 12 spaces, `log_status()` will be inserted with the exact same indentation as `start_process()` relative to the patch structure.

### Common Mistakes (Anti-Patterns)

#### Wrong Context Location (`-v2 -insert`)
**Mistake:** Inserting into a block where the surrounding lines imply a different indentation Delta than expected.

**Target File:**
```python
def process():
    if check:
        do_it()
    # <-- You want to insert here, outside the 'if' (4 spaces)
```

**Bad Patch:**
```
<@|EDIT -v2 -insert script.py
---old---
        do_it()
{code_start|content|code_end}
---new---
    cleanup()
---end---
```

**What Happens:**
The anchor is `do_it()` (8 spaces). The patcher calculates Delta relative to this line. If you provided `cleanup()` with 4 spaces in `---new---`, it *might* work, but if you provided it with 0 spaces in the patch thinking it's absolute, the Delta logic might shift it to 8 spaces (aligning with `do_it`), keeping it inside the `if`.

**Fix:** Always verify what the "Anchor" line is. If you want to break out of a nesting level (dedent), ensure your context includes the line *causing* the scope (e.g., the `if` statement) or manually adjust indentation in `---new---` to match the visual delta you want.

### Examples

#### Example 1: Inserting into a Loop (V2)
Inserting code inside a loop without knowing the surrounding indentation depth.

**Target File:**
```python
    # Arbitrary indentation level
    for user in users:
        send_email(user)
        # <--- We want to insert logging here
```

**The Patch:**
```
<@|EDIT -v2 -insert task.py
---old---
send_email(user)
{code_start|content|code_end}
---new---
print(f"Email sent to {user}")
---end---
```

**Result:**
The `print` statement will effectively inherit the indentation of `send_email(user)`.

#### Removal (`-remove`)
Finds and removes the code block specified in `---old---`.

```
<-@ Find and remove the outdated function @->
<@|EDIT -remove @ROOT/utils.py
---old---
def old_function():
    # some legacy code
    pass
---end---
```


---

## The `REFACTOR` Command

A high-level command for smart code modification using AST (Abstract Syntax Tree) analysis. Unlike `EDIT`, it understands code structure (classes, functions, identifiers) rather than just text.

### Arguments
- `-rename <Old> to <New>`: Renames variables, classes, or functions intelligently.

- `-inject`: Inserts code based on logical structure rather than text matching.

- `-imports`: Manages Python imports (update, add, remove).


### Variables
- `---files---`: List of files to process (if `-project` is not used).
- `---ignore---`: List of identifiers or context lines to skip.

- `---files---`: List of target files/patterns.
- `---content---`: The code to inject.

- `---files---`: (Optional) Explicit list of files to process for `-add` or `-remove`.


#### Smart Rename (`-rename`)

Renames identifiers (variables, functions, classes) across specific files or the entire project using AST analysis. This ensures that only actual code identifiers are renamed, avoiding matches in strings or comments (unlike simple text replacement).

**Syntax:**
`REFACTOR -rename <OldName> to <NewName> [-project] [-ignore]`

**Modifiers:**
*   `-project`: Scans all supported files in `@ROOT`. If omitted, requires `---files---` block.
*   `-ignore`: Enables the `---ignore---` block to exclude specific matches.

**Blocks:**
*   `---files---`: List of files to process (if `-project` is not used).
*   `---ignore---`: List of identifiers to skip if found.

### Examples

#### Example 1: Rename a Class Project-Wide
Renames the class `BaseConfig` to `AppConfig` in all files, but keeps `OldBaseConfig` untouched using ignore.

```
<@|REFACTOR -rename <BaseConfig> to <AppConfig> -project -ignore
---ignore---
BaseConfig_Backup
OldBaseConfig
---end---
```

#### Example 2: Rename a Function in Specific Files
Renames `calculate` to `calc_metric` only in the specified paths.

```
<@|REFACTOR -rename <calculate> to <calc_metric>
---files---
@ROOT/core/utils.py
@ROOT/core/math_lib.py
---end---
```

#### Example 3: Rename a Variable
Renames `data` to `payload` inside a specific script.

```
<@|REFACTOR -rename <data> to <payload>
---files---
@ROOT/api/handler.py
---end---
```


#### Structural Injection (`-inject`)

Inserts code into classes or modules based on AST structure. Unlike `EDIT`, it operates on logical blocks (classes, functions), allowing insertions at specific structural positions (start, end, or relative to other members).

**Syntax:**
`REFACTOR -inject -type <class|func> -search_type <code|class> -pos <Position> ...`

**Arguments:**
*   `-type <class|func>`: Specifies the type of the *content being inserted*.
    *   `class`: Ensures correct spacing for top-level classes (e.g., 2 empty lines).
    *   `func`: Ensures correct spacing for methods/functions (e.g., 1 empty line inside class, 2 at root).
*   `-search_type <code|class>`: Defines the scope where the anchor or insertion point is located.
    *   `code`: Searches in the global file scope (root). Use this to add new classes or functions to the file.
    *   `<class Name>`: Searches inside the specified class. Use this to add methods to a class.
*   `-pos <Position>`: Defines where to insert relative to the `search_type` scope.
    *   `<top:Anchor A|bottom:Anchor B>`: Inserts *between* Anchor A and Anchor B.
    *   `<start>`: Inserts at the beginning of the scope (e.g., first method in a class).
    *   `<end>`: Inserts at the end of the scope (e.g., last method in a class).
    *   **Anchor Format:** `type Name` (e.g., `def my_method`, `class MyClass`).

**Blocks:**
*   `---files---`: List of target files/patterns.
*   `---content---`: The code to inject.

### Examples

#### Example 1: Add a new function to the end of a file
Adds a `main` function to the end of the module.

```
<@|REFACTOR -inject -type func -search_type <code> -pos <end>
---files---
@ROOT/app.py
---content---
def main():
    print("App started")
---end---
```

#### Example 2: Add a method to a class
Adds a `to_string` method to the end of the `User` class.

```
<@|REFACTOR -inject -type func -search_type <class User> -pos <end>
---files---
@ROOT/models/user.py
---content---
    def to_string(self):
        return f"User: {self.name}"
---end---
```

#### Example 3: Insert a method between others
Inserts `pre_process` inside the `Worker` class, placing it between `__init__` and `process`.

```
<@|REFACTOR -inject -type func -search_type <class Worker> -pos <top:def __init__|bottom:def process>
---files---
@ROOT/core/worker.py
---content---
    def pre_process(self):
        print("Pre-processing...")
---end---
```


#### Imports Management (`-imports`)

Automates updating, adding, or removing imports across multiple files. It handles indentation and placement automatically.

**Syntax:**
`REFACTOR -imports [-update <old> to <new>] [-add <mod> to <scope>] [-remove <mod>]`

**Arguments:**
*   `-update <old> to <new>`: Renames a module in import statements.
    *   Example: `-update <utils> to <core.utils>`
*   `-add <module> to <scope>`: Adds `import module` if it is missing.
    *   `scope`: Can be a directory (`@ROOT/src`) or file (`@ROOT/main.py`). The import is added to all Python files in that scope.
*   `-remove <module>`: Removes lines importing this module from the project (or specified files).

**Blocks:**
*   `---files---`: (Optional) Explicit list of files to process. Overrides scanning logic for `-remove` or provides specific targets for other ops.

### Examples

#### Example 1: Update Import Path
Changes all occurrences of `import utils` to `import core.utils` in the project.

```
<@|REFACTOR -imports -update <utils> to <core.utils>
---end---
```

#### Example 2: Add Import to a Folder
Adds `import logging` to all Python files in the `src` folder if it's missing.

```
<@|REFACTOR -imports -add <logging> to <@ROOT/src>
---end---
```

#### Example 3: Remove Unused Import
Removes `import pdb` from specific files.

```
<@|REFACTOR -imports -remove <pdb>
---files---
@ROOT/main.py
@ROOT/tests/test_api.py
---end---
```
