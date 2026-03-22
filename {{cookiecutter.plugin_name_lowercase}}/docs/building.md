# Building {{cookiecutter.plugin_name}}

## Prerequisites

- **CMake 3.22+**
- **C++{{cookiecutter.cpp_standard}} compiler** (Clang, GCC, or MSVC)
- **[just](https://github.com/casey/just)** command runner (recommended)
- **[Ninja](https://ninja-build.org/)** build system (recommended)
{% if cookiecutter.include_faust == "yes" -%}
- **[Faust](https://faust.grame.fr/downloads/)** (only needed when modifying the DSP)
{% endif %}
### Platform-Specific

- **macOS**: Xcode Command Line Tools (`xcode-select --install`)
- **Windows**: Visual Studio 2019+ with C++ desktop workload
- **Linux**: Build essentials + JUCE dependencies:
  ```bash
  sudo apt-get install -y \
    libasound2-dev libx11-dev libxcomposite-dev libxcursor-dev \
    libxext-dev libxinerama-dev libxrandr-dev libxrender-dev \
    libfreetype6-dev libglu1-mesa-dev mesa-common-dev \
    libcurl4-openssl-dev libwebkit2gtk-4.1-dev
  ```

## Quick Start

```bash
just build          # Configure + build (Debug)
just release        # Configure + build (Release)
just run            # Build + launch standalone
just clean          # Remove build directory
just rebuild        # Clean + full rebuild
```

## CMake Options

| Option | Default | Description |
|--------|---------|-------------|
| `{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD` | `ON` | Copy plugin to system dirs after build |
| `{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE` | `ON` | Use `-march=native` (disable for distributable builds) |
{% if cookiecutter.include_faust == "yes" -%}
| `{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN` | `ON` | Run Faust codegen (requires `faust` on PATH) |
{% endif -%}
| `{{cookiecutter.plugin_name | upper}}_FORMATS` | `"{% if cookiecutter.include_vst2 == "yes" %}VST {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3 {% endif %}{% if cookiecutter.include_au == "yes" %}AU {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}"` | Plugin formats to build |

## CI / Distributable Builds

For CI or distribution, disable machine-specific optimizations:

```bash
cmake -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -D{{cookiecutter.plugin_name | upper}}_COPY_AFTER_BUILD=OFF \
  -D{{cookiecutter.plugin_name | upper}}_USE_MARCH_NATIVE=OFF{% if cookiecutter.include_faust == "yes" %} \
  -D{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=OFF{% endif %}

cmake --build build --config Release --parallel
```

This uses SSE4.2 as the baseline for x86_64 (broad compatibility) instead of `-march=native`.

## DSP Optimization Flags

The CMake build applies these optimizations automatically for Release builds:

| Compiler | Flags | Purpose |
|----------|-------|---------|
| Clang/GCC | `-O3 -ffast-math -funroll-loops` | Auto-vectorization of DSP loops |
| Clang/GCC (x86 dev) | `-march=native` | Target exact CPU (AVX2/FMA) |
| Clang/GCC (x86 CI) | `-msse4.2` | Broad compatibility baseline |
| Clang | `-fdenormal-fp-math=positive-zero` | Flush denormals to zero |
| MSVC | `/O2 /fp:fast` | Fast float + full optimization |
| MSVC (dev) | `/arch:AVX2` | AVX2 instructions |

ARM64 (Apple Silicon) has NEON enabled by default — no extra flags needed.
