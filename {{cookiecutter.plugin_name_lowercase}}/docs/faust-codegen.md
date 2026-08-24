# Faust Codegen Pipeline

{{cookiecutter.plugin_name}} uses Faust for DSP and generates JUCE bridge headers for parameter/state integration.

## Outputs

Generated into `src/dsp/generated/`:

- `FaustDefs.h`
- `FaustDSP.h`
- `FaustParams.h`
- `FaustBridge.h`

These files are committed so CI builds do not require Faust.

## Run Codegen

```bash
just codegen
```

or

```bash
python3 scripts/codegen.py dsp/{{cookiecutter.faust_dsp_name}}.dsp --output src/dsp/generated
```

## Build Integration

When `{{cookiecutter.plugin_name | upper}}_ENABLE_CODEGEN=ON`, CMake re-runs codegen when either:

- `dsp/{{cookiecutter.faust_dsp_name}}.dsp` changes
- `scripts/codegen.py` changes

If `faust` is not installed, CMake falls back to committed generated headers.

## Performance Details in Generated Bridge

- Stable parameter IDs from explicit Faust metadata (`[id:...]`) when available.
- Cached APVTS raw parameter pointers for lower process-block overhead.
- In-place processing fast path when layout allows.
- Scratch-buffer fallback for non-ideal host channel layout.

## Compiler Flags Used for Faust C++ Generation

```bash
faust -lang cpp -cn {{cookiecutter.faust_class_name}} -scn "" -vec -vs 32 -lv 1 -ftz 0 -mcd 0 -single -uim
```

## Post-Processing

After generating `FaustDSP.h`, the script:

1. injects `#include "FaustDefs.h"`
2. suppresses unused `sample_rate` warnings in Faust helper SIG methods

## Targeting a Different Sample Rate (e.g. an Embedded Build)

Faust has no compiler-define mechanism for injecting a value like a target
sample rate at compile time (`ma.SR` isn't known until runtime, long after
codegen runs). If `{{cookiecutter.faust_dsp_name}}.dsp` declares delay-line
buffers following the convention

```faust
MAX_SOMETHING = 96000; // 500 ms @ 192 kHz
```

(a `MAX_*` constant with a `// X ms @ Y kHz` comment), `--max-sample-rate`
rewrites that constant for a different target ceiling before compiling:

```bash
python3 scripts/codegen.py dsp/{{cookiecutter.faust_dsp_name}}.dsp \
    --output src/dsp/generated --max-sample-rate 48000
```

This is a no-op if no such constants exist yet -- the default starter `.dsp` has
none. Generated output from a non-default `--max-sample-rate` is stamped with a
`CUSTOM CODEGEN BUILD` banner so it's never confused with the desktop build's
committed files.
{% if cookiecutter.include_daisy == "yes" %}
See `daisy/README.md` for the Daisy Seed scaffold that uses this flag.
{% endif %}
