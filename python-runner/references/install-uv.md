# Installing uv

## Quick Install (Recommended)

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If curl isn't available:
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Alternative Methods

**Homebrew (macOS):**
```bash
brew install uv
```

**pip (any platform):**
```bash
pip install uv
```

**pipx (isolated install):**
```bash
pipx install uv
```

## Verify Installation

```bash
uv --version
```

## Upgrading

If installed via standalone installer:
```bash
uv self update
```

If installed via pip:
```bash
pip install --upgrade uv
```

If installed via Homebrew:
```bash
brew upgrade uv
```