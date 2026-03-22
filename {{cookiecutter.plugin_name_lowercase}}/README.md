# {{cookiecutter.plugin_name}}

{{cookiecutter.plugin_description}}

## About

- **Author**: {{cookiecutter.author_name}} ({{cookiecutter.author_email}})
- **Company**: {{cookiecutter.company_name}}
- **Formats**: {% if cookiecutter.include_vst2 == "yes" %}VST2, {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3, {% endif %}{% if cookiecutter.include_au == "yes" %}AU, {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}

## Prerequisites

- CMake 3.22 or higher
- C++{{cookiecutter.cpp_standard}} compatible compiler
- [just](https://github.com/casey/just) command runner (recommended)
- macOS: Xcode Command Line Tools
- Windows: Visual Studio 2019 or later
- Linux: GCC or Clang
{% if cookiecutter.include_faust == "yes" -%}
- [Faust](https://faust.grame.fr/downloads/) (only needed to modify the DSP)
{% endif %}
{% if cookiecutter.include_vst2 == "yes" -%}
## VST2 Setup

To build VST2 plugins, add and initialize the VST2 SDK submodule:

```bash
git submodule add https://github.com/sysfce2/vst-2.4-sdk.git external/vst-2.4-sdk
git submodule update --init --recursive
```
{% endif %}
## Building

### Quick Start (with just)

```bash
just build          # Debug build
just release        # Release build
just run            # Build and launch standalone
just clean          # Remove build directory
```

### Manual CMake

```bash
cmake -B build -G Ninja
cmake --build build --config Release
```

### CI / Distributable Builds

```bash
cmake -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -D{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD=OFF \
  -D{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE=OFF{% if cookiecutter.include_faust == "yes" %} \
  -D{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=OFF{% endif %}

cmake --build build --config Release --parallel
```
{% if cookiecutter.include_faust == "yes" %}
## Faust DSP

The DSP is written in [Faust](https://faust.grame.fr/). A codegen script bridges Faust's generated C++ with JUCE's parameter system.

- Edit `dsp/{{cookiecutter.faust_dsp_name}}.dsp`
- Run `just codegen` (or just rebuild — CMake triggers it automatically)
- Generated bridge files live in `src/dsp/generated/`
- **You do not need Faust installed to build** — generated files are committed to git

See [docs/faust-codegen.md](docs/faust-codegen.md) for full details.
{% endif %}
### Development with Element.app

For rapid iteration with Element.app DAW:

```bash
cp scripts/element_project.conf.example scripts/element_project.conf
# Edit scripts/element_project.conf with your .els project path
just element
```

## Project Structure

```
{{cookiecutter.plugin_name_lowercase}}/
├── CMakeLists.txt              # Build configuration
├── justfile                    # Task runner recipes
{% if cookiecutter.include_faust == "yes" -%}
├── dsp/
│   └── {{cookiecutter.faust_dsp_name}}.dsp  # Faust DSP source
{% endif -%}
├── src/
│   ├── PluginProcessor.h/cpp   # Audio processing
│   ├── PluginEditor.h/cpp      # UI editor
│   ├── components/
│   │   ├── brand/
│   │   │   └── TopBar.h/cpp    # Top bar with logo
│   │   ├── controls/           # UI controls (knobs, sliders, etc.)
│   │   └── graphs/             # Visualizations (waveforms, spectrums)
│   ├── data/                   # Data models and state
{% if cookiecutter.include_faust == "yes" -%}
│   ├── dsp/
│   │   └── generated/          # Auto-generated Faust bridge headers
{% else -%}
│   ├── dsp/                    # DSP processing (filters, effects)
{% endif -%}
│   └── utils/                  # Utilities and helpers
├── assets/
│   └── images/
│       └── logo.png            # Company logo
├── scripts/
{% if cookiecutter.include_faust == "yes" -%}
│   ├── codegen.py              # Faust -> JUCE bridge codegen
│   └── element_dev.sh          # Build & reload script
{% else -%}
│   └── element_dev.sh          # Build & reload script
{% endif -%}
{% if cookiecutter.include_faust == "yes" -%}
├── docs/
│   └── faust-codegen.md        # Codegen pipeline documentation
{% endif -%}
└── external/                   # Git submodules
{% if cookiecutter.include_vst2 == "yes" %}    └── vst-2.4-sdk/            # VST2 SDK{% endif %}
```

## License

[Your License Here]
