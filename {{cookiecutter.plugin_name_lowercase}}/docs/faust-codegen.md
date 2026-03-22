# Faust Codegen Pipeline

{{cookiecutter.plugin_name}}'s DSP is written in [Faust](https://faust.grame.fr/), a functional DSP language. A codegen script bridges the gap between Faust's generated C++ and JUCE's parameter system, so the two can talk to each other without manual wiring.

## Overview

The pipeline has two stages:

1. **Faust compiler** (`faust`) compiles `dsp/{{cookiecutter.faust_dsp_name}}.dsp` into a C++ DSP class
2. **`scripts/codegen.py`** reads the Faust JSON metadata and generates JUCE integration headers

The output is 4 header files in `src/dsp/generated/`:

| File | Purpose |
|---|---|
| `FaustDefs.h` | Minimal `UI` and `Meta` stubs so the Faust output compiles without the Faust SDK |
| `FaustDSP.h` | The Faust-compiled C++ DSP class (`{{cookiecutter.faust_class_name}}`) |
| `FaustParams.h` | APVTS `ParameterLayout` + string constant parameter IDs, derived from Faust metadata |
| `FaustBridge.h` | Bridge class that syncs APVTS parameter values to Faust's internal zones each audio block |

These files are committed to git. **You do not need Faust installed to build the plugin.** Faust is only needed when you want to change the DSP.

## How It Works

Faust DSP parameters are declared with metadata like:

```faust
gain = hslider("[01] Gain", 1.0, 0.0, 1.0, 0.01) : si.smoo;
```

The Faust compiler emits a JSON file containing the full UI tree -- parameter names, ranges, defaults, and the internal variable names (e.g. `fHslider0`) that map to memory zones in the generated C++ class.

`codegen.py` reads this JSON and generates:

- **Parameter IDs**: `"[01] Gain"` becomes `FaustParamIDs::gain` (`"gain"`)
- **APVTS layout**: Creates `AudioParameterFloat` / `AudioParameterBool` entries with the correct ranges
- **Bridge sync**: Maps each APVTS parameter to its Faust zone variable (`dsp_.fHslider0 = *apvts_.getRawParameterValue(FaustParamIDs::gain)`)
- **Typed getters**: `float getGain()`, etc.

The naming convention uses camelCase for parameter IDs and PascalCase for getter methods, derived from the Faust label text.

## Running Codegen

Install [Faust](https://faust.grame.fr/downloads/) and make sure `faust` is on your PATH. Then:

```bash
just codegen
```

Or directly:

```bash
python3 scripts/codegen.py dsp/{{cookiecutter.faust_dsp_name}}.dsp --output src/dsp/generated
```

### Automatic Trigger

When `{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=ON` (the default), CMake registers a custom command that re-runs codegen whenever `dsp/{{cookiecutter.faust_dsp_name}}.dsp` or `scripts/codegen.py` changes. So during normal development, just edit the `.dsp` and rebuild -- codegen runs automatically.

If Faust isn't installed, CMake falls back to the committed generated files silently.

## Faust Compiler Flags

The codegen script invokes Faust with these flags:

```
faust -lang cpp -cn {{cookiecutter.faust_class_name}} -scn "" -vec -vs 32 -lv 1 -ftz 0 -mcd 0 -single -uim
```

| Flag | Purpose |
|---|---|
| `-lang cpp` | C++ output |
| `-cn {{cookiecutter.faust_class_name}}` | Generated class name |
| `-scn ""` | No base class -- makes the output self-contained (no Faust SDK dependency) |
| `-vec -vs 32` | Vectorized inner loops, vector size 32 (good for NEON and AVX2) |
| `-lv 1` | Simple vector loop variant (best for compiler auto-vectorization) |
| `-ftz 0` | Flush-to-zero OFF in generated code (handled by JUCE `ScopedNoDenormals` + compiler flags instead) |
| `-mcd 0` | Disable max copy delay optimization (better for vectorized code) |
| `-single` | Single precision (`float`) |
| `-uim` | Generate UI metadata in the C++ output |

### Post-Processing

After Faust generates `FaustDSP.h`, codegen.py does two fixups:

1. Injects `#include "FaustDefs.h"` after the header guard so the `UI`/`Meta` stubs are available
2. Adds `(void)sample_rate;` to suppress `-Wunused-parameter` warnings in Faust's internal SIG helper methods

## Workflow

1. Edit `dsp/{{cookiecutter.faust_dsp_name}}.dsp`
2. Test in the [Faust IDE](https://faustide.grame.fr/) if you want quick feedback
3. Run `just codegen` (or just rebuild -- CMake triggers it automatically)
4. Build and test the plugin
5. Commit the updated generated files along with your `.dsp` changes

The generated files should always be committed so that contributors and CI can build without installing Faust.
