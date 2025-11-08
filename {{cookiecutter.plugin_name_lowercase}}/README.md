# {{cookiecutter.plugin_name}}

{{cookiecutter.plugin_description}}

## About

- **Author**: {{cookiecutter.author_name}} ({{cookiecutter.author_email}})
- **Company**: {{cookiecutter.company_name}}
- **Formats**: {% if cookiecutter.include_vst2 == "yes" %}VST2, {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3, {% endif %}{% if cookiecutter.include_au == "yes" %}AU, {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}

## Building

This project uses CMake and fetches JUCE automatically.

### Prerequisites

- CMake 3.22 or higher
- C++{{cookiecutter.cpp_standard}} compatible compiler
- macOS: Xcode Command Line Tools
- Windows: Visual Studio 2019 or later
- Linux: GCC or Clang
{% if cookiecutter.include_vst2 == "yes" %}
### VST2 Setup (Optional)

To build VST2 plugins, initialize the VST2 SDK submodule:

```bash
git submodule update --init --recursive
```
{% endif %}
### Build Steps

```bash
# Configure
cmake -B build

# Build
cmake --build build --config Release
```

### Development Build Script

For rapid iteration with Element.app DAW:

```bash
# Optional: Configure Element project path
cp scripts/element_project.conf.example scripts/element_project.conf
# Edit scripts/element_project.conf with your .els project path

# Build and reload in Element
./scripts/element_dev.sh
```

## Project Structure

```
{{cookiecutter.plugin_name_lowercase}}/
├── CMakeLists.txt              # Build configuration
├── src/
│   ├── PluginProcessor.h/cpp   # Audio processing
│   ├── PluginEditor.h/cpp      # UI editor
│   ├── components/
│   │   ├── brand/
│   │   │   └── TopBar.h/cpp    # Top bar with logo
│   │   ├── controls/           # UI controls (knobs, sliders, etc.)
│   │   └── graphs/             # Visualizations (waveforms, spectrums)
│   ├── data/                   # Data models and state
│   ├── dsp/                    # DSP processing (filters, effects)
│   └── utils/                  # Utilities and helpers
├── assets/
│   └── images/
│       └── logo.png            # Company logo
├── scripts/
│   └── element_dev.sh          # Build & reload script
└── external/                   # Git submodules
{% if cookiecutter.include_vst2 == "yes" %}    └── vst-2.4-sdk/            # VST2 SDK{% endif %}
```

## License

[Your License Here]
