# Building {{cookiecutter.plugin_name}}

## Prerequisites

- CMake 3.22+
- C++{{cookiecutter.cpp_standard}} compiler (Clang/GCC/MSVC)
- Ninja (recommended)
- just (recommended)
{% if cookiecutter.include_faust == "yes" -%}
- Faust (only needed when changing DSP)
{% endif %}

## Quick Start

```bash
just build
just release
just run
```

## CMake Options

| Option | Default | Description |
|---|---|---|
| `{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD` | `ON` | Copy plugin to system directories |
| `{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE` | `ON` | Machine-specific optimization for local builds |
| `{{cookiecutter.plugin_name | upper}}_ENABLE_IPO` | `ON` | Enable LTO/IPO in Release when available |
{% if cookiecutter.include_faust == "yes" -%}
| `{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN` | `ON` | Run Faust codegen if `faust` is on PATH |
{% endif -%}
{% if cookiecutter.include_vst2 == "yes" -%}
| `{{cookiecutter.plugin_name | upper}}_ENABLE_VST2` | `OFF` | Enable VST2 if SDK checkout exists |
{% endif -%}
| `{{cookiecutter.plugin_name | upper}}_FORMATS` | format list | Space-separated plugin formats |

## CI / Distributable Builds

```bash
cmake -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -D{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD=OFF \
  -D{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE=OFF{% if cookiecutter.include_faust == "yes" %} \
  -D{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=OFF{% endif %}

cmake --build build --config Release --parallel
```

## Optimization Notes

- Clang/GCC: `-O3 -ffast-math -ffp-contract=fast -fno-math-errno -funroll-loops`
- x86_64 local: `-march=native`
- x86_64 CI/distribution: `-msse4.2`
- Clang denormal handling: `-fdenormal-fp-math=positive-zero`
- MSVC: `/O2 /fp:fast` (+ `/arch:AVX2` when enabled)

## CI Pipeline

The generated GitHub workflow builds:

- macOS universal
- macOS legacy x86_64
- Windows
- Linux (+ pluginval VST3 validation)

It also supports:

- `workflow_dispatch` release runs
- draft release packaging for `v*` tags
- tag verification/creation for manual release dispatch
