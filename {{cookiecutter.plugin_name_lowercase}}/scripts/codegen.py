{% raw %}#!/usr/bin/env python3
"""
Faust -> JUCE Parameter Bridge Code Generator

Reads Faust JSON metadata and generates:
  - FaustParams.h  (APVTS parameter layout + param ID constants)
  - FaustBridge.h  (bridge class: APVTS <-> Faust DSP zones)

Also invokes the Faust compiler to generate FaustDSP.h.
"""

import argparse
import json
import math
import os
import re
import subprocess

from typing import Any


def label_to_param_id(label: str) -> str:
    s = label.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def label_to_camel(label: str) -> str:
    snake = label_to_param_id(label)
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def label_to_pascal(label: str) -> str:
    snake = label_to_param_id(label)
    return "".join(p.capitalize() for p in snake.split("_"))


def get_meta_value(param: dict[str, Any], key: str) -> str | None:
    for meta_entry in param.get("meta", []):
        if key in meta_entry:
            return str(meta_entry[key])
    return None


def get_param_id(param: dict[str, Any]) -> str:
    explicit_id = get_meta_value(param, "id")
    if explicit_id:
        return label_to_param_id(explicit_id)
    return label_to_param_id(param["label"])


def param_id_to_camel(param_id: str) -> str:
    return label_to_camel(param_id)


def param_id_to_pascal(param_id: str) -> str:
    return label_to_pascal(param_id)


def extract_params(ui_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    params = []
    for item in ui_items:
        item_type = item.get("type", "")
        if item_type in ("vgroup", "hgroup", "tgroup"):
            params.extend(extract_params(item.get("items", [])))
        elif item_type in ("hslider", "vslider", "nentry", "checkbox", "button"):
            params.append(item)
    return params


def extract_bargraphs(ui_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bargraphs = []
    for item in ui_items:
        item_type = item.get("type", "")
        if item_type in ("vgroup", "hgroup", "tgroup"):
            bargraphs.extend(extract_bargraphs(item.get("items", [])))
        elif item_type in ("hbargraph", "vbargraph"):
            bargraphs.append(item)
    return bargraphs


def get_sort_key(param: dict[str, Any]) -> int:
    for meta_entry in param.get("meta", []):
        for key in meta_entry:
            if key.isdigit():
                return int(key)
    return 99


# Matches a "MAX_SOMETHING = N; // X ms @ Y kHz" convention for delay-line buffer
# constants, if the .dsp source happens to use one (see docs/faust-codegen.md).
# Not every DSP has delay lines -- this is opt-in via --max-sample-rate, and it's
# fine for zero matches to mean "nothing to resize" rather than an error.
MAX_DELAY_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<name>MAX_\w+)(?P<sp>[ \t]*)=[ \t]*\d+;[ \t]*"
    r"//[ \t]*(?P<ms>\d+)[ \t]*ms[ \t]*@[ \t]*[\d.]+[ \t]*kHz",
    re.MULTILINE,
)


def rewrite_max_delay_constants_for_sample_rate(source: str, max_sample_rate: int) -> tuple[str, int]:
    """Resizes MAX_*_DELAY-style buffers for a target max sample rate instead of
    whatever ceiling the .dsp file's comments assume (typically 192 kHz, sized for
    an arbitrary desktop DAW session rate).

    Faust has no compiler-define mechanism for injecting a value like this at
    compile time (`ma.SR` isn't known until runtime, long after codegen runs), so
    this does the substitution ourselves before the source ever reaches `faust`.
    Meant for a fixed-sample-rate embedded target (e.g. Daisy Seed at 48 kHz),
    where carrying a buffer sized for a desktop-worst-case rate wastes memory a
    fixed-rate target will never need.

    Returns (rewritten_source, number_of_constants_rewritten).
    """
    def replace(match: re.Match) -> str:
        ms = int(match.group("ms"))
        samples = math.ceil(ms * max_sample_rate / 1000.0)
        khz = max_sample_rate / 1000.0
        khz_str = f"{khz:g}"
        return (
            f"{match.group('indent')}{match.group('name')}{match.group('sp')}"
            f"= {samples}; // {ms} ms @ {khz_str} kHz"
        )

    new_source, count = MAX_DELAY_LINE_RE.subn(replace, source)
    return new_source, count


def run_faust_cpp(
    dsp_path: str,
    output_path: str,
    class_name: str = "{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}",
    build_note: str | None = None,
) -> None:
    cmd = [
        "faust",
        "-lang",
        "cpp",
        "-uim",
        "-cn",
        class_name,
        "-scn",
        "",
        "-vec",
        "-vs",
        "32",
        "-lv",
        "1",
        "-ftz",
        "0",
        "-mcd",
        "0",
        "-single",
        "-o",
        output_path,
        dsp_path,
    ]
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    with open(output_path, "r") as f:
        content = f.read()

    guard_pattern = f"#define  __{class_name}_H__"
    faust_defs_include = '#include "FaustDefs.h"'
    if build_note:
        # Loud, hard-to-miss marker that this isn't the default desktop build --
        # the buffer sizes below were resized for a specific target sample rate
        # and would silently clamp shorter than labeled at any higher rate.
        faust_defs_include = (
            "// ==========================================================================\n"
            f"// CUSTOM CODEGEN BUILD -- {build_note}\n"
            "// Do not commit this over the default generated output.\n"
            "// ==========================================================================\n"
            f"{faust_defs_include}"
        )
    if guard_pattern in content:
        content = content.replace(
            guard_pattern,
            f"{guard_pattern}\n\n{faust_defs_include}",
        )
    else:
        content = content.replace(
            "#endif \n\n/* link with",
            f"{faust_defs_include}\n\n#endif \n\n/* link with",
        )

    content = re.sub(
        r"(void instanceInit\w+SIG\d+\(int sample_rate\) \{)",
        r"\1\n\t\t(void)sample_rate;",
        content,
    )

    content = re.sub(
        r"(static void classInit\(int sample_rate\) \{)",
        r"\1\n\t\t(void)sample_rate;",
        content,
    )

    with open(output_path, "w") as f:
        f.write(content)


def run_faust_json(dsp_path: str, output_dir: str) -> str:
    # IMPORTANT: the flags here must match run_faust_cpp() exactly so that
    # the varname fields (fVslider0, fVslider1, ...) in the JSON correspond
    # to the same variables in the generated C++ DSP.  Different compilation
    # options (especially -vec, -mcd) cause Faust to assign variable names
    # in a different order.
    cmd = [
        "faust",
        "-json",
        "-vec",
        "-vs",
        "32",
        "-lv",
        "1",
        "-ftz",
        "0",
        "-mcd",
        "0",
        "-single",
        "-o",
        "/dev/null",
        dsp_path,
    ]
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    src_json = dsp_path + ".json"
    if not os.path.exists(src_json):
        raise FileNotFoundError(f"Expected JSON output at {src_json}")

    dst_json = os.path.join(output_dir, os.path.basename(src_json))
    os.replace(src_json, dst_json)
    return dst_json


FAUST_DEFS_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py -- do not edit manually.
// Minimal type stubs so the Faust-generated DSP compiles without the Faust SDK.
// ==========================================================================
#pragma once

#ifndef FAUSTFLOAT
#define FAUSTFLOAT float
#endif

struct UI {
    virtual ~UI() = default;
    virtual void openTabBox(const char*) {}
    virtual void openHorizontalBox(const char*) {}
    virtual void openVerticalBox(const char*) {}
    virtual void closeBox() {}
    virtual void addButton(const char*, FAUSTFLOAT*) {}
    virtual void addCheckButton(const char*, FAUSTFLOAT*) {}
    virtual void addVerticalSlider(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addHorizontalSlider(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addNumEntry(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addHorizontalBargraph(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addVerticalBargraph(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addSoundfile(const char*, const char*, void**) {}
    virtual void declare(FAUSTFLOAT*, const char*, const char*) {}
};

struct Meta {
    virtual ~Meta() = default;
    virtual void declare(const char*, const char*) {}
};
"""


def generate_faust_defs_h() -> str:
    return FAUST_DEFS_HEADER


PARAMS_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py from {dsp_name} -- do not edit manually.
// ==========================================================================
#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

namespace FaustParamIDs {{
{param_id_constants}
}} // namespace FaustParamIDs

namespace FaustParams {{

inline juce::AudioProcessorValueTreeState::ParameterLayout createLayout()
{{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

{param_layout_entries}
    return {{ params.begin(), params.end() }};
}}

}} // namespace FaustParams
"""


def generate_params_h(params: list[dict[str, Any]], dsp_name: str) -> str:
    id_lines = []
    for p in params:
        pid = get_param_id(p)
        camel = param_id_to_camel(pid)
        id_lines.append(f'    static constexpr const char* {camel} = "{pid}";')

    layout_lines = []
    for p in params:
        pid = get_param_id(p)
        camel = param_id_to_camel(pid)
        ptype = p["type"]

        if ptype == "checkbox" or ptype == "button":
            # Check for [default:1] metadata to set initial state
            default_val = "false"
            for meta_entry in p.get("meta", []):
                if "default" in meta_entry and str(meta_entry["default"]) == "1":
                    default_val = "true"
            layout_lines.append(
                f"    params.push_back(std::make_unique<juce::AudioParameterBool>(\n"
                f"        juce::ParameterID{{FaustParamIDs::{camel}, 1}},\n"
                f'        "{p["label"]}",\n'
                f"        {default_val}));"
            )
        else:
            init_val = float(p.get("init", 0))
            min_val = float(p.get("min", 0))
            max_val = float(p.get("max", 1))
            step_val = float(p.get("step", 0.01))
            scale = get_meta_value(p, "scale")
            if scale == "log" and max_val > min_val:
                # Compute skew factor that centres the knob on the geometric mean.
                # JUCE formula: skew = log(0.5) / log((centre - min) / (max - min))
                centre = math.sqrt(min_val * max_val)
                skew = math.log(0.5) / math.log(
                    (centre - min_val) / (max_val - min_val)
                )
                range_str = (
                    f"juce::NormalisableRange<float>"
                    f"({min_val}f, {max_val}f, {step_val}f, {skew:.4f}f)"
                )
            else:
                range_str = (
                    f"juce::NormalisableRange<float>"
                    f"({min_val}f, {max_val}f, {step_val}f)"
                )
            layout_lines.append(
                f"    params.push_back(std::make_unique<juce::AudioParameterFloat>(\n"
                f"        juce::ParameterID{{FaustParamIDs::{camel}, 1}},\n"
                f'        "{p["label"]}",\n'
                f"        {range_str},\n"
                f"        {init_val}f));"
            )

    return PARAMS_HEADER.format(
        dsp_name=dsp_name,
        param_id_constants="\n".join(id_lines),
        param_layout_entries="\n".join(layout_lines),
    )


BRIDGE_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py from {dsp_name} -- do not edit manually.
// ==========================================================================
#pragma once

#include "FaustDefs.h"
#include "FaustDSP.h"
#include "FaustParams.h"

#include <atomic>
#include <juce_audio_processors/juce_audio_processors.h>

class FaustBridge {{
public:
    explicit FaustBridge(juce::AudioProcessorValueTreeState& apvts)
        : apvts_(apvts)
    {{
{cached_param_init_lines}
    }}

    void prepare(double sampleRate, int samplesPerBlock)
    {{
        dsp_.init(static_cast<int>(sampleRate));
        resizeScratchBuffers(samplesPerBlock);
    }}

    void process(juce::AudioBuffer<float>& buffer, int numInputChannels, int numOutputChannels)
    {{
        const int numSamples = buffer.getNumSamples();

{sync_lines}

        float* inputChannels[{num_inputs}];
        float* outputChannels[{num_outputs}];

        const bool canProcessInPlace = numInputChannels >= {num_inputs} && numOutputChannels >= {num_outputs};
        if (canProcessInPlace) {{
            for (int ch = 0; ch < {num_inputs}; ++ch)
                inputChannels[ch] = buffer.getWritePointer(ch);
            for (int ch = 0; ch < {num_outputs}; ++ch)
                outputChannels[ch] = buffer.getWritePointer(ch);
        }} else {{
            resizeScratchBuffers(numSamples);

            for (int ch = 0; ch < {num_inputs}; ++ch) {{
                auto* scratch = inputScratch_.getWritePointer(ch);
                if (numInputChannels <= 0) {{
                    juce::FloatVectorOperations::clear(scratch, numSamples);
                    continue;
                }}

                const int sourceChannel = juce::jmin(ch, numInputChannels - 1);
                juce::FloatVectorOperations::copy(scratch, buffer.getReadPointer(sourceChannel), numSamples);
            }}

            for (int ch = 0; ch < {num_inputs}; ++ch)
                inputChannels[ch] = inputScratch_.getWritePointer(ch);
            for (int ch = 0; ch < {num_outputs}; ++ch)
                outputChannels[ch] = outputScratch_.getWritePointer(ch);
        }}

        dsp_.compute(numSamples, inputChannels, outputChannels);

        if (!canProcessInPlace) {{
            for (int ch = 0; ch < juce::jmin(numOutputChannels, {num_outputs}); ++ch)
                buffer.copyFrom(ch, 0, outputScratch_.getReadPointer(ch), numSamples);
        }}
    }}

    {class_name}& getDSP() {{ return dsp_; }}
    const {class_name}& getDSP() const {{ return dsp_; }}

{getter_methods}

private:
    static float loadParam(const std::atomic<float>* param, float fallback = 0.0f) noexcept
    {{
        return param != nullptr ? param->load(std::memory_order_relaxed) : fallback;
    }}

    void resizeScratchBuffers(int numSamples)
    {{
        const int requiredSamples = juce::jmax(1, numSamples);
        if (inputScratch_.getNumSamples() < requiredSamples)
            inputScratch_.setSize({num_inputs}, requiredSamples, false, false, true);
        if (outputScratch_.getNumSamples() < requiredSamples)
            outputScratch_.setSize({num_outputs}, requiredSamples, false, false, true);
    }}

    {class_name} dsp_;
    juce::AudioProcessorValueTreeState& apvts_;
{cached_param_ptr_lines}
    juce::AudioBuffer<float> inputScratch_;
    juce::AudioBuffer<float> outputScratch_;
}};
"""


def generate_bridge_h(
    params: list[dict[str, Any]],
    bargraphs: list[dict[str, Any]],
    dsp_name: str,
    class_name: str = "{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}",
    num_inputs: int = 2,
    num_outputs: int = 2,
) -> str:
    sync_lines = []
    cached_param_init_lines = []
    cached_param_ptr_lines = []
    for p in params:
        pid = get_param_id(p)
        camel = param_id_to_camel(pid)
        varname = p["varname"]
        ptype = p["type"]
        cached_name = f"{camel}Param_"

        cached_param_init_lines.append(
            f"        {cached_name} = apvts_.getRawParameterValue(FaustParamIDs::{camel});"
        )
        cached_param_ptr_lines.append(f"    std::atomic<float>* {cached_name} = nullptr;")

        if ptype == "checkbox" or ptype == "button":
            sync_lines.append(
                f"        dsp_.{varname} = loadParam({cached_name}) > 0.5f ? 1.0f : 0.0f;"
            )
        else:
            sync_lines.append(
                f"        dsp_.{varname} = loadParam({cached_name});"
            )

    getter_lines = []
    for p in params:
        pid = get_param_id(p)
        camel = param_id_to_camel(pid)
        pascal = param_id_to_pascal(pid)
        ptype = p["type"]

        if ptype == "checkbox" or ptype == "button":
            getter_lines.append(
                f"    bool get{pascal}() const {{ return loadParam({camel}Param_) > 0.5f; }}"
            )
        else:
            getter_lines.append(
                f"    float get{pascal}() const {{ return loadParam({camel}Param_); }}"
            )

    # Deduplicate bargraphs with the same id (e.g. stereo GR meters).
    # When duplicates exist, generate per-channel getters (L/R) plus a
    # combined getter that returns the min (most-compressed) value.
    seen_bargraph_ids: dict[str, list[dict[str, Any]]] = {}
    for b in bargraphs:
        bid = get_param_id(b)
        seen_bargraph_ids.setdefault(bid, []).append(b)

    for bid, bg_list in seen_bargraph_ids.items():
        pascal = param_id_to_pascal(bid)
        if len(bg_list) == 1:
            varname = bg_list[0]["varname"]
            getter_lines.append(
                f"    float get{pascal}() const {{ return dsp_.{varname}; }}"
            )
        else:
            # Per-channel getters (L, R, ...)
            suffixes = ["L", "R", "C", "Ls", "Rs", "Lfe"]  # extend if > stereo
            varnames = []
            for i, b in enumerate(bg_list):
                suffix = suffixes[i] if i < len(suffixes) else str(i)
                varname = b["varname"]
                varnames.append(varname)
                getter_lines.append(
                    f"    float get{pascal}{suffix}() const {{ return dsp_.{varname}; }}"
                )
            # Combined getter: min of all channels (most gain reduction)
            min_expr = ", ".join(f"dsp_.{v}" for v in varnames)
            getter_lines.append(
                f"    float get{pascal}() const {{ return juce::jmin({min_expr}); }}"
            )

    return BRIDGE_HEADER.format(
        dsp_name=dsp_name,
        class_name=class_name,
        num_inputs=num_inputs,
        num_outputs=num_outputs,
        cached_param_init_lines="\n".join(cached_param_init_lines),
        cached_param_ptr_lines="\n".join(cached_param_ptr_lines),
        sync_lines="\n".join(sync_lines),
        getter_methods="\n".join(getter_lines),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Faust -> JUCE parameter bridge codegen"
    )
    parser.add_argument("dsp_file", help="Path to the .dsp file")
    parser.add_argument(
        "--output", "-o", required=True, help="Output directory for generated files"
    )
    parser.add_argument(
        "--class-name",
        default="{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}",
        help="C++ class name for the Faust DSP",
    )
    parser.add_argument(
        "--skip-faust",
        action="store_true",
        help="Skip running faust compiler (use existing .json and FaustDSP.h)",
    )
    parser.add_argument(
        "--max-sample-rate",
        type=int,
        default=None,
        help=(
            "Resize any 'MAX_* = N; // X ms @ Y kHz' delay-line buffers in the "
            ".dsp source for this target sample rate instead of whatever ceiling "
            "the comments already assume. Use for a fixed-rate embedded target "
            "(e.g. --max-sample-rate 48000 for a Daisy Seed build) to avoid "
            "carrying memory sized for a rate that will never occur. No-op if "
            "the .dsp has no such constants. Omit for the normal desktop build."
        ),
    )
    args = parser.parse_args()

    dsp_path = os.path.abspath(args.dsp_file)
    output_dir = os.path.abspath(args.output)
    build_note: str | None = None
    rewritten_dsp_path: str | None = None

    if args.max_sample_rate is not None:
        with open(dsp_path, "r") as f:
            original_source = f.read()

        rewritten_source, rewritten_count = rewrite_max_delay_constants_for_sample_rate(
            original_source, args.max_sample_rate
        )
        if rewritten_count == 0:
            print(
                f"[codegen] --max-sample-rate {args.max_sample_rate} given but no "
                "'MAX_* = N; // X ms @ Y kHz' constants were found -- nothing to resize."
            )
        else:
            rewritten_dsp_path = os.path.join(
                os.path.dirname(dsp_path), f".codegen-tmp.{os.path.basename(dsp_path)}"
            )
            with open(rewritten_dsp_path, "w") as f:
                f.write(rewritten_source)

            build_note = f"MAX_*_DELAY sized for {args.max_sample_rate} Hz"
            print(f"[codegen] CUSTOM SAMPLE RATE BUILD: {build_note}")

    # dsp_name feeds the "AUTO-GENERATED from {dsp_name}" banners -- always the
    # real source file's name, never the temp rewritten copy's.
    dsp_name = os.path.basename(dsp_path)
    if rewritten_dsp_path is not None:
        dsp_path = rewritten_dsp_path

    class_name = args.class_name

    os.makedirs(output_dir, exist_ok=True)

    try:
        faust_dsp_h = os.path.join(output_dir, "FaustDSP.h")
        if not args.skip_faust:
            print("[codegen] Running Faust compiler...")
            run_faust_cpp(dsp_path, faust_dsp_h, class_name, build_note=build_note)

            print("[codegen] Generating Faust JSON metadata...")
            json_path = run_faust_json(dsp_path, output_dir)
        else:
            json_path = os.path.join(output_dir, os.path.basename(dsp_path) + ".json")
            print(f"[codegen] Skipping Faust compiler, reading existing {json_path}")

        print(f"[codegen] Reading {json_path}...")
        with open(json_path, "r") as f:
            faust_json = json.load(f)
    finally:
        if rewritten_dsp_path is not None and os.path.exists(rewritten_dsp_path):
            os.remove(rewritten_dsp_path)

    ui_tree = faust_json.get("ui", [])
    params = extract_params(ui_tree)
    params.sort(key=get_sort_key)
    bargraphs = extract_bargraphs(ui_tree)
    bargraphs.sort(key=get_sort_key)

    num_inputs = faust_json.get("inputs", 2)
    num_outputs = faust_json.get("outputs", 2)

    print(
        f"[codegen] Found {len(params)} parameters, {len(bargraphs)} bargraphs, {num_inputs} inputs, {num_outputs} outputs"
    )

    defs_h = generate_faust_defs_h()
    defs_path = os.path.join(output_dir, "FaustDefs.h")
    with open(defs_path, "w") as f:
        f.write(defs_h)

    params_h = generate_params_h(params, dsp_name)
    params_path = os.path.join(output_dir, "FaustParams.h")
    with open(params_path, "w") as f:
        f.write(params_h)

    bridge_h = generate_bridge_h(params, bargraphs, dsp_name, class_name, num_inputs, num_outputs)
    bridge_path = os.path.join(output_dir, "FaustBridge.h")
    with open(bridge_path, "w") as f:
        f.write(bridge_h)

    print("[codegen] Done.")


if __name__ == "__main__":
    main()
{% endraw %}
