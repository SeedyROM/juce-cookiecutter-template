// {{cookiecutter.plugin_name}} — Daisy Seed firmware scaffold.
//
// UNVERIFIED: written as a template without libDaisy or an ARM toolchain
// available to compile against, so nothing here has actually been built. It
// shows the integration pattern (feed {{cookiecutter.faust_class_name}} from
// libDaisy's audio callback, place its state in SDRAM if it grows large, read
// pots into its parameter fields) -- confirm every libDaisy API call below
// against whatever version you have checked out. Field/class names in
// particular (AudioHandle::InputBuffer, DSY_SDRAM_BSS, etc.) have moved between
// libDaisy releases.
//
// Regenerate generated/FaustDSP.h and generated/FaustDefs.h first:
//   python3 ../scripts/codegen.py ../dsp/{{cookiecutter.faust_dsp_name}}.dsp \
//       --output generated --max-sample-rate 48000
// See README.md for why this needs its own codegen output rather than
// src/dsp/generated/ (the desktop plugin's files pull in JUCE headers this
// bare-metal build doesn't have).

#include "daisy_seed.h"

#include "generated/FaustDSP.h"

using namespace daisy;

DaisySeed hw;

// SDRAM placement: once {{cookiecutter.faust_class_name}} holds real delay-line
// or buffer state, it likely won't fit in the Seed's internal SRAM/DTCM.
// DSY_SDRAM_BSS places this instance in the external SDRAM section instead --
// confirm the macro's exact name and header in your libDaisy version (it wraps
// a plain `__attribute__((section(".sdram_bss")))`; see README.md). Harmless
// to leave in place even before the DSP has grown large enough to need it.
{{cookiecutter.faust_class_name}} DSY_SDRAM_BSS dsp;

// Faust's generated class expects a UI to call add*Slider/addCheckButton on
// during init -- FaustDefs.h's no-op stubs satisfy that (see
// docs/faust-codegen.md for why those exist). This firmware never builds a
// real UI object; it pokes the resulting f* member fields directly instead.
static UI unusedFaustUi;

void AudioCallback(AudioHandle::InputBuffer in,
                    AudioHandle::OutputBuffer out,
                    size_t size) {
  // Pot/CV reads belong here, once per block, mapped to whichever hardware
  // input your build actually wires up. One example -- confirm the exact
  // field name against generated/FaustDSP.h after regenerating; Faust assigns
  // fHsliderN/fCheckboxN indices by declaration order in the .dsp, and they
  // are not guaranteed stable if parameters are added or reordered.
  //
  //   dsp.fHslider0 = hw.adc.GetFloat(0);  // whichever parameter that is
  //
  // Every parameter in {{cookiecutter.faust_dsp_name}}.dsp follows the same
  // pattern: one pot (or a fixed default) feeding one f* field, read once per
  // block rather than per-sample, same as FaustBridge::process() does for the
  // JUCE build.

  float* inputChannels[2] = {const_cast<float*>(in[0]), const_cast<float*>(in[1])};
  float* outputChannels[2] = {out[0], out[1]};

  dsp.compute(static_cast<int>(size), inputChannels, outputChannels);
}

int main(void) {
  hw.Init();
  hw.SetAudioBlockSize(48); // start conservative; profile before shrinking
  hw.SetAudioSampleRate(SaiHandle::Config::SampleRate::SAI_48KHZ);

  dsp.init(static_cast<int>(hw.AudioSampleRate()));

  // Faust's instanceInit/instanceConstants run against the UI stub above once,
  // the same role FaustBridge::prepare() plays on the JUCE side -- confirm
  // {{cookiecutter.faust_class_name}}'s actual init entry point name in the
  // regenerated header; Faust's C++ backend has changed this signature across
  // versions.

  hw.StartAudio(AudioCallback);

  while (1) {
    // Non-audio work (reading buttons, updating an LED, MIDI if added later)
    // goes here, same as it would in any libDaisy example.
  }
}
