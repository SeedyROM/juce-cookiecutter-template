# JUCE Cookiecutter Template

A cookiecutter template for creating JUCE audio plugins with modern CI, CLAP support, optional Faust codegen, always-on preset/A-B architecture, and optional advanced themed UI.

Generates VST2, VST3, AU, CLAP and Standalone builds from one CMake project, so a small
Faust or C++ DSP idea reaches every format anyone is likely to ask for.

## Features

- **Modern CMake setup** with FetchContent and CI-friendly options.
- **CI/release pipeline** for macOS, Windows, Linux, plus Linux pluginval validation.
- **Faust codegen support** (optional) with generated bridge headers committed for CI-safe builds.
- **Preset + A/B architecture** included by default in every generated project.
- **Advanced UI profile** (`include_advanced_ui`) with custom controls, look-and-feel, and meter visuals.
- **CLAP support** (`include_clap`) via [clap-juce-extensions](https://github.com/free-audio/clap-juce-extensions), fetched at configure time, with real parameter ranges exported to the host.
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

- **Minimal profile:** `include_advanced_ui=no`, `include_faust=no`, `include_clap=no`
- **Most-post profile:** `include_advanced_ui=yes`, `include_faust=yes`, `include_ci=yes`, `include_clap=yes`

`include_clap=yes` needs network access on the first CMake configure, since the wrapper
is fetched rather than vendored. Set it to `no` for an offline-buildable project.

## New Template Options

- `include_advanced_ui`: include rich editor controls, custom look-and-feel, and color constants.
- `include_clap`: build a CLAP alongside the JUCE formats. CLAP is not a JUCE format, so
  it sits outside `<PLUGIN>_FORMATS` and has its own `<PLUGIN>_ENABLE_CLAP` switch. The
  clap-juce-extensions dependency is pinned to a commit rather than a tag, because that
  repository's tags are CLAP *spec* versions from 2022 rather than releases — building
  against one silently produces a pre-CLAP-1.0 wrapper.

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
