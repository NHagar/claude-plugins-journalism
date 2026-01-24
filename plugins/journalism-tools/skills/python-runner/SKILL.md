---
name: python-runner
description: Run Python scripts with automatic dependency management using uv. Use when executing Python code that may have package dependencies, when the user doesn't have a Python environment set up, or when you need isolated script execution without polluting system packages. Handles dependency installation automatically—no manual pip install or virtual environment setup required.
---

# Running Python Scripts with uv

Execute Python scripts with automatic, isolated dependency management. No manual environment setup required.

## Quick Reference

```bash
# Check if uv is available
uv --version

# Run script without dependencies
uv run script.py

# Run script with dependencies (installed automatically)
uv run --with pandas --with requests script.py

# Run with specific Python version
uv run --python 3.11 script.py
```

If uv is not installed, see `references/install-uv.md`.

## Recommended Approach: Inline Dependencies

Embed dependencies directly in the script so it's self-contained and reproducible:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pandas",
#   "requests",
# ]
# ///

import pandas as pd
import requests

# ... rest of script
```

Then run with just:
```bash
uv run script.py
```

uv automatically creates an isolated environment with the declared dependencies.

## Adding Dependencies to Scripts

Use `uv add --script` to add dependencies to an existing script:

```bash
# Add single dependency
uv add --script script.py pandas

# Add multiple with version constraints
uv add --script script.py 'requests<3' 'rich>=13'
```

This inserts/updates the `# /// script` metadata block at the top of the file.

## Common Patterns

### Data analysis script
```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pandas",
#   "openpyxl",  # for Excel support
# ]
# ///

import pandas as pd

df = pd.read_excel("data.xlsx")
print(df.describe())
```

### Web scraping script
```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///

import requests
from bs4 import BeautifulSoup

resp = requests.get("https://example.com")
soup = BeautifulSoup(resp.text, "lxml")
```

### PDF processing script
```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pdfplumber",
#   "pandas",
# ]
# ///

import pdfplumber
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
```

## Command Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--with pkg` | Add dependency for this run only | `uv run --with rich script.py` |
| `--python X.Y` | Use specific Python version | `uv run --python 3.11 script.py` |
| `--no-project` | Ignore pyproject.toml in directory | `uv run --no-project script.py` |

## Passing Arguments to Scripts

Arguments after the script name pass through to the script:

```bash
uv run script.py input.csv --output results.json
```

In the script:
```python
import sys
print(sys.argv)  # ['script.py', 'input.csv', '--output', 'results.json']
```

## Troubleshooting

**"uv: command not found"**
→ uv not installed. See `references/install-uv.md`

**Module not found errors**
→ Add missing package to dependencies block or use `--with`

**Wrong Python version**
→ Specify version: `uv run --python 3.11 script.py`
→ Or add `requires-python` to script metadata

**Script in a project directory picks up wrong dependencies**
→ Use `--no-project` flag before script name
