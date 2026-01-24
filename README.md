# Journalism Tools for Claude Code

A plugin marketplace with tools for investigative journalism: Python script execution with automatic dependency management, data preprocessing with provenance tracking, and transparent data analysis designed to be defensible under scrutiny.

## Installation

Add the marketplace and install the plugin:

```shell
/plugin marketplace add nhagar/claude-plugins-journalism
/plugin install journalism-tools@journalism-tools
```

## Skills

Once installed, you'll have access to three skills:

### `/journalism-tools:python-runner`

Run Python scripts with automatic dependency management using [uv](https://github.com/astral-sh/uv). No manual environment setup required—dependencies are installed automatically in isolated environments.

### `/journalism-tools:journalistic-data-preprocessing`

Preprocessing workflow for journalistic data analysis emphasizing transparency, provenance, and human oversight. Core principles:

- **Provenance first**: Every row traces to source file, sheet, and row number
- **No silent transformations**: Every change is documented and approved
- **Human-in-the-loop**: Present findings and get approval before transformations
- **Transparency artifacts**: Generate documentation suitable for reporters and editors

### `/journalism-tools:structured-data-analysis-journalism`

Analyze preprocessed data for investigative journalism with full transparency. Emphasizes simple, legible analyses over complex methods—every finding must be explainable to editors and defensible under scrutiny. Core principles:

- **Simple beats clever**: Analyses must be explainable in plain language
- **Every number needs a source**: Statistics trace back to verifiable records
- **Findings are hypotheses**: Analysis surfaces patterns, not proof of wrongdoing
- **Defensibility over sophistication**: Simple analyses that hold up under scrutiny

## Local Development

Test the plugin locally without installing:

```bash
claude --plugin-dir ./plugins/journalism-tools
```

## License

MIT
