// {{cookiecutter.plugin_name}} — Faust DSP
// Minimal stereo passthrough with a single gain parameter.
// Edit this file, then run `just codegen` (or rebuild) to regenerate
// the JUCE parameter bridge in src/dsp/generated/.

import("stdfaust.lib");

gain = hslider("[01] Gain", 1.0, 0.0, 1.0, 0.01) : si.smoo;

process = _, _ : *(gain), *(gain);
