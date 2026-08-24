# {{cookiecutter.plugin_name}} on Daisy Seed — starting scaffold

**Status: unverified template.** Nothing in this directory has been built against
a real ARM toolchain or libDaisy checkout — it's a documented starting point for
porting `{{cookiecutter.faust_dsp_name}}.dsp` to Daisy Seed, not a finished port.
Confirm every libDaisy API call in `main.cpp` against whatever version you have
checked out before trusting it; names in libDaisy's audio callback and SDRAM
placement macros have moved between releases.

## What this is

The plugin's DSP (`dsp/{{cookiecutter.faust_dsp_name}}.dsp`) compiles to a
self-contained C++ class (`{{cookiecutter.faust_class_name}}`) with zero JUCE
dependency — see `docs/faust-codegen.md`. That class is exactly what a Daisy Seed
firmware needs; this directory wires it to `libDaisy` instead of to JUCE's
`AudioProcessor`.

## Why this needs its own codegen output, not `src/dsp/generated/`

The committed `src/dsp/generated/` files are sized for the *desktop* plugin: any
delay-line buffers in the `.dsp` follow whatever sample-rate ceiling the source
comments assume (see `docs/faust-codegen.md` for the `MAX_* = N; // X ms @ Y kHz`
convention this expects), because a DAW session's sample rate isn't known until
runtime. Daisy Seed runs at one fixed rate you choose at build time (48 kHz is
libDaisy's default), so carrying a buffer sized for a much higher desktop ceiling
wastes memory for headroom you'll never use. Regenerate for this target
specifically:

```bash
python3 ../scripts/codegen.py ../dsp/{{cookiecutter.faust_dsp_name}}.dsp \
    --output generated \
    --max-sample-rate 48000
```

(`just daisy-codegen` runs the same command — see the project's `justfile`.) This
produces `generated/FaustDSP.h` and `generated/FaustDefs.h`, stamped with a
`CUSTOM CODEGEN BUILD` banner so they're never confused with the desktop files. If
`{{cookiecutter.faust_dsp_name}}.dsp` has no `MAX_*` delay-line constants (the
default starter `.dsp` doesn't — it's a plain gain stage), this step is a no-op;
add the convention yourself once you add delay lines that need it.

**Do not use `generated/FaustParams.h` or `FaustBridge.h`** even though codegen
produces them — both `#include <juce_audio_processors/juce_audio_processors.h>`,
which doesn't exist in a bare-metal ARM build. This firmware talks to
`{{cookiecutter.faust_class_name}}` directly and maps hardware controls to its
`f*` member fields itself (see `main.cpp`), with no APVTS layer in between.

## SDRAM placement

Once your DSP grows real delay-line state (a looper, a long delay, a big reverb
tank), it likely won't fit in the Daisy Seed's internal SRAM (a few hundred KB).
libDaisy provides a section-attribute macro for placing large buffers in the
external SDRAM instead — confirm the exact name in your checked-out libDaisy
source (it has moved between releases; search for `SDRAM` in `daisy_seed.h` or
`daisy_core.h`). The pattern, regardless of exact macro name:

```cpp
// Placed in the .sdram_bss linker section instead of internal SRAM/DTCM.
{{cookiecutter.faust_class_name}} DSY_SDRAM_BSS dsp;
```

If your libDaisy version doesn't expose a ready-made macro, the underlying GCC
attribute it wraps is:

```cpp
__attribute__((section(".sdram_bss")))
```

Confirm the target's linker script actually maps `.sdram_bss` to the SDRAM
address range — libDaisy's default linker script for the Seed does this out of
the box, but a customized one might not.

## Build

Daisy Seed firmware conventionally builds via a Makefile against
`libDaisy`/`DaisySP`, not CMake — see
[Electrosmith's getting-started guide](https://github.com/electro-smith/DaisyExamples)
for toolchain setup (`arm-none-eabi-gcc`, `dfu-util` or `stlink` for flashing).
`Makefile` in this directory is a starting stub; set `LIBDAISY_DIR` in it (or via
`make LIBDAISY_DIR=...`) to point at your actual libDaisy checkout, then:

```bash
just daisy-build   # regenerates DSP for 48kHz, then builds the firmware
```

## What's deliberately not here

- Control mapping (which pot/CV input drives which parameter) — `main.cpp` shows
  the pattern for one parameter; the rest follow identically, but actual pin
  assignments depend on the physical hardware you're building.
- Preset storage, MIDI, or any of the JUCE-side plugin features (A/B slots,
  presets) — none of that has a Daisy equivalent here yet.
- Verification that the DSP fits comfortably within the audio callback's
  real-time budget at 48 kHz on the target chip. Desktop CPU headroom does not
  transfer to an embedded target — profile on real hardware, don't assume.
