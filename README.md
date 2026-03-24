# JUCE Cookiecutter Template

A cookiecutter template for creating JUCE audio plugins with modern CI, optional Faust codegen, always-on preset/A-B architecture, and optional advanced themed UI.

## Features

- **Modern CMake setup** with FetchContent and CI-friendly options.
- **CI/release pipeline** for macOS, Windows, Linux, plus Linux pluginval validation.
- **Faust codegen support** (optional) with generated bridge headers committed for CI-safe builds.
- **Preset + A/B architecture** included by default in every generated project.
- **Advanced UI profile** (`include_advanced_ui`) with custom controls, look-and-feel, and meter visuals.
## Usage

### Prerequisites

- Python 3.x
- cookiecutter (`pip install cookiecutter`)
- CMake 3.22+
- C++17 compatible compiler

### Create a Plugin

```bash
cookiecutter https://github.com/SeedyROM/juce-cookiecutter-template
```

### Recommended Profiles

- **Minimal profile:** `include_advanced_ui=no`, `include_faust=no`
- **Most-post profile:** `include_advanced_ui=yes`, `include_faust=yes`, `include_ci=yes`

## New Template Options

- `include_advanced_ui`: include rich editor controls, custom look-and-feel, and color constants.

## Architecture Notes

- Preset files are stored per generated plugin under `<UserData>/<Company>/<Plugin>/Presets`.
- Preset extension is plugin-specific: `.<plugin_name_lowercase>preset`.
- Processor state includes schema-wrapped A/B slot state and preset labels.
- Advanced UI is optional, but processor/preset/A-B architecture is always included.

## Testing

```bash
uv run pytest -v
```

Slow configure test:

```bash
uv run pytest -v -m slow
```

## License

Apache-2.0 License. See `LICENSE` for details.
