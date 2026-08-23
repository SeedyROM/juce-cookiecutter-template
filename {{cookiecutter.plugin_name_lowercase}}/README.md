# {{cookiecutter.plugin_name}}

{{cookiecutter.plugin_description}}

## About

- **Author**: {{cookiecutter.author_name}} ({{cookiecutter.author_email}})
- **Company**: {{cookiecutter.company_name}}
- **Formats**: {% if cookiecutter.include_vst2 == "yes" %}VST2, {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3, {% endif %}{% if cookiecutter.include_au == "yes" %}AU, {% endif %}{% if cookiecutter.include_clap == "yes" %}CLAP, {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}

## Architecture Included

- **Preset + A/B state architecture** is included by default.
- **Preset storage path**: `~/Library/Application Support/{{cookiecutter.company_name}}/{{cookiecutter.plugin_name}}/Presets` (platform equivalent).
- **Preset extension**: `.{{cookiecutter.plugin_name_lowercase}}preset`.
- **Advanced UI profile**: `{% if cookiecutter.include_advanced_ui == "yes" %}enabled{% else %}disabled{% endif %}`.

{% if cookiecutter.include_advanced_ui == "yes" -%}
## Theming

The advanced UI uses color constants (`src/ui/{{cookiecutter.plugin_name}}Colors.h`) and a custom look-and-feel (`src/ui/PluginLookAndFeel.*`).
{% endif %}

## Prerequisites

- CMake 3.22+
- C++{{cookiecutter.cpp_standard}} compiler
- [just](https://github.com/casey/just) (recommended)
{% if cookiecutter.include_faust == "yes" -%}
- [Faust](https://faust.grame.fr/downloads/) (only needed when editing DSP)
{% endif %}

## Build

```bash
just build
just release
just run
```

Manual:

```bash
cmake -B build -G Ninja
cmake --build build --config Release
```

{% if cookiecutter.include_clap == "yes" -%}
## CLAP

Built through [clap-juce-extensions](https://github.com/free-audio/clap-juce-extensions),
which CMake fetches at configure time -- no submodule, but it does need network access
on the first configure. CLAP is not a JUCE format, so it sits outside
`{{cookiecutter.plugin_name | upper}}_FORMATS` and has its own switch:

```bash
just plugin_enable_clap=OFF build      # or -D{{cookiecutter.plugin_name | upper}}_ENABLE_CLAP=OFF
```

Parameters are exported with their real JUCE ranges rather than normalised 0-1, so a
host shows `-4.3 dB` instead of `0.41`. That choice is baked into how automation is
stored, so change it only before there are sessions to break.

Known gap: clap-juce-extensions does not map JUCE's `getBypassParameter()` onto
`CLAP_PARAM_IS_BYPASS`, so a CLAP host's own bypass button is not bound to the plugin's
bypass parameter. The parameter is still present and automatable. VST3 and AU are
unaffected.
{% endif %}
## CI/Distribution Build

```bash
cmake -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -D{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD=OFF \
  -D{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE=OFF{% if cookiecutter.include_faust == "yes" %} \
  -D{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=OFF{% endif %}
```

## Presets and A/B

- A/B state architecture exists in the processor backend.
- No presets are pre-populated in the advanced UI template shell.
- Preset behavior is intended to be defined by the plugin implementation.

## Advanced UI

{% if cookiecutter.include_advanced_ui == "yes" -%}
Enabled in this generated project:

- Themed top bar with preset/A-B/options controls wired as placeholders.
- Empty content area below top bar for product-specific UI.
- Color constants and look-and-feel infrastructure ready for customization.
{% else -%}
Disabled in this generated project. To enable in a new generation, set `include_advanced_ui=yes`.
{% endif %}

## Project Structure

```
{{cookiecutter.plugin_name_lowercase}}/
├── CMakeLists.txt
├── justfile
├── src/
│   ├── PluginProcessor.h/cpp
│   ├── PluginEditor.h/cpp
│   ├── presets/
│   │   └── PluginPresetManager.h/cpp
│   ├── data/
│   │   ├── PluginParameters.h
│   │   └── RuntimeParameters.h
│   ├── components/
│   │   ├── brand/TopBar.h/cpp
{% if cookiecutter.include_advanced_ui == "yes" -%}
│   │   └── controls/RotaryKnob.h/cpp
│   └── ui/{{cookiecutter.plugin_name}}Colors.h, PluginLookAndFeel.h/cpp
{% endif -%}
{% if cookiecutter.include_faust == "yes" -%}
├── dsp/{{cookiecutter.faust_dsp_name}}.dsp
├── src/dsp/generated/
├── scripts/codegen.py
{% endif -%}
└── scripts/element_dev.sh
```

## License

[Your License Here]
