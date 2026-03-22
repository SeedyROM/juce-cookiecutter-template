{% set UPPER = cookiecutter.plugin_name | upper -%}
cmake_minimum_required(VERSION 3.22)

project({{cookiecutter.plugin_name}} VERSION 0.1.0)

# Suppress developer warnings from JUCE
set(CMAKE_SUPPRESS_DEVELOPER_WARNINGS ON CACHE INTERNAL "")

set(CMAKE_CXX_STANDARD {{cookiecutter.cpp_standard}})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

{% if cookiecutter.include_vst2 == "yes" -%}
# VST2 SDK Path - must be set BEFORE fetching JUCE
set(VST2_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/external/vst-2.4-sdk/vstsdk2.4" CACHE PATH "Path to VST2 SDK")

if(EXISTS "${VST2_SDK_PATH}/pluginterfaces/vst2.x/aeffect.h")
    message(STATUS "VST2 SDK found at: ${VST2_SDK_PATH}")
else()
    message(WARNING "VST2 SDK not found at: ${VST2_SDK_PATH}")
    message(WARNING "Run: git submodule update --init --recursive")
endif()

{% endif -%}
# CI-friendly options
option({{ UPPER }}_COPY_AFTER_BUILD "Copy plugin to system dirs after build" ON)
option({{ UPPER }}_USE_MARCH_NATIVE "Use -march=native (disable for distributable builds)" ON)
{% if cookiecutter.include_faust == "yes" -%}
option({{ UPPER }}_ENABLE_CODEGEN "Run Faust codegen (requires faust on PATH)" ON)
{% endif -%}
set({{ UPPER }}_FORMATS "{% if cookiecutter.include_vst2 == "yes" %}VST {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3 {% endif %}{% if cookiecutter.include_au == "yes" %}AU {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}" CACHE STRING "Plugin formats to build")

# Fetch JUCE from GitHub (release archive — fast, no git overhead)
include(FetchContent)
FetchContent_Declare(
    JUCE
    URL https://github.com/juce-framework/JUCE/archive/refs/tags/{{cookiecutter.juce_version}}.tar.gz
)
FetchContent_MakeAvailable(JUCE)

{% if cookiecutter.include_vst2 == "yes" -%}
# Set VST2 SDK path for JUCE (must be after FetchContent_MakeAvailable)
if(EXISTS "${VST2_SDK_PATH}/pluginterfaces/vst2.x/aeffect.h")
    juce_set_vst2_sdk_path("${VST2_SDK_PATH}")
endif()

{% endif -%}
{% if cookiecutter.include_faust == "yes" -%}
# ==========================================================================
# Faust DSP Codegen
# ==========================================================================
# Regenerates the Faust C++ DSP and JUCE parameter bridge when the .dsp changes.
# The generated files are committed to git, so Faust is only needed when
# modifying the DSP source. Disable with -D{{ UPPER }}_ENABLE_CODEGEN=OFF for CI.

set(FAUST_GEN_DIR "${CMAKE_SOURCE_DIR}/src/dsp/generated")

if({{ UPPER }}_ENABLE_CODEGEN)
    find_program(FAUST_EXECUTABLE faust)
    if(FAUST_EXECUTABLE)
        message(STATUS "Faust found: ${FAUST_EXECUTABLE} — codegen enabled")

        set(FAUST_DSP "${CMAKE_SOURCE_DIR}/dsp/{{cookiecutter.faust_dsp_name}}.dsp")
        set(FAUST_CODEGEN "${CMAKE_SOURCE_DIR}/scripts/codegen.py")

        set(FAUST_GENERATED_FILES
            ${FAUST_GEN_DIR}/FaustDefs.h
            ${FAUST_GEN_DIR}/FaustDSP.h
            ${FAUST_GEN_DIR}/FaustParams.h
            ${FAUST_GEN_DIR}/FaustBridge.h
        )

        add_custom_command(
            OUTPUT ${FAUST_GENERATED_FILES}
            COMMAND ${CMAKE_COMMAND} -E make_directory ${FAUST_GEN_DIR}
            COMMAND python3 ${FAUST_CODEGEN} ${FAUST_DSP} --output ${FAUST_GEN_DIR}
            DEPENDS ${FAUST_DSP} ${FAUST_CODEGEN}
            COMMENT "Generating Faust DSP and parameter bridge from {{cookiecutter.faust_dsp_name}}.dsp..."
            VERBATIM
        )

        add_custom_target(faust_codegen DEPENDS ${FAUST_GENERATED_FILES})
    else()
        message(STATUS "Faust not found — codegen disabled, using committed generated files")
    endif()
else()
    message(STATUS "Faust codegen disabled ({{ UPPER }}_ENABLE_CODEGEN=OFF)")
endif()

{% endif -%}
# ==========================================================================
# Plugin Target
# ==========================================================================

# Convert formats string to a list for juce_add_plugin
separate_arguments({{ UPPER }}_FORMATS_LIST UNIX_COMMAND "${{"{"}}{{ UPPER }}_FORMATS}")

# Define the plugin
juce_add_plugin({{cookiecutter.plugin_name}}
    COMPANY_NAME "{{cookiecutter.company_name}}"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD ${{"{"}}{{ UPPER }}_COPY_AFTER_BUILD}
    PLUGIN_MANUFACTURER_CODE {{cookiecutter.plugin_manufacturer_code}}
    PLUGIN_CODE {{cookiecutter.plugin_code}}
    FORMATS ${{"{"}}{{ UPPER }}_FORMATS_LIST}
    PRODUCT_NAME "{{cookiecutter.plugin_name}}"
)

{% if cookiecutter.include_faust == "yes" -%}
# Ensure codegen runs before compiling plugin sources (only if target exists)
if(TARGET faust_codegen)
    add_dependencies({{cookiecutter.plugin_name}} faust_codegen)
endif()

{% endif -%}
# Add binary resources (fonts, images, etc)
juce_add_binary_data({{cookiecutter.plugin_name}}Assets SOURCES
    assets/images/logo.png
)

# Add source files
target_sources({{cookiecutter.plugin_name}} PRIVATE
    src/PluginProcessor.cpp
    src/PluginEditor.cpp
    src/components/brand/TopBar.cpp
)

# Include paths
target_include_directories({{cookiecutter.plugin_name}} PRIVATE
{% if cookiecutter.include_faust == "yes" -%}
    ${FAUST_GEN_DIR}
{% endif -%}
    ${CMAKE_SOURCE_DIR}/src
)

# Set compile definitions
target_compile_definitions({{cookiecutter.plugin_name}} PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
)

# ==========================================================================
# DSP Optimization Flags
# ==========================================================================
# These flags enable the compiler to fully auto-vectorize DSP code using
# SIMD instructions (NEON on Apple Silicon, AVX2/SSE on x86).

# -ffast-math: enables FP contraction, reciprocal approximations, and
#              reassociation — critical for auto-vectorization of DSP code.
#              Safe here because we control the numeric range (audio floats).
# -march=native: target the build machine's exact CPU (enables AVX2, NEON, etc.)
# -funroll-loops: unroll inner DSP loops for better ILP and SIMD utilization.

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options({{cookiecutter.plugin_name}} PRIVATE
        # Release-only optimizations
        $<$<CONFIG:Release>:-O3>
        $<$<CONFIG:Release>:-ffast-math>
        $<$<CONFIG:Release>:-funroll-loops>
    )

    # Architecture-specific SIMD flags
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "arm64|aarch64")
        # Apple Silicon / ARM64: NEON is always available, no extra flags needed.
        message(STATUS "Target: ARM64 (NEON intrinsics available by default)")
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
        if({{ UPPER }}_USE_MARCH_NATIVE)
            # Local dev builds: target exact CPU for max performance
            target_compile_options({{cookiecutter.plugin_name}} PRIVATE
                $<$<CONFIG:Release>:-march=native>
            )
            message(STATUS "Target: x86_64 (using -march=native for AVX2/FMA)")
        else()
            # CI / distributable builds: SSE4.2 baseline for broad compatibility
            target_compile_options({{cookiecutter.plugin_name}} PRIVATE
                $<$<CONFIG:Release>:-msse4.2>
            )
            message(STATUS "Target: x86_64 (using SSE4.2 baseline for distribution)")
        endif()
    endif()

    # Flush-to-zero at the compiler level
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        target_compile_options({{cookiecutter.plugin_name}} PRIVATE
            $<$<CONFIG:Release>:-fdenormal-fp-math=positive-zero>
        )
    endif()
elseif(MSVC)
    target_compile_options({{cookiecutter.plugin_name}} PRIVATE
        $<$<CONFIG:Release>:/O2>
        $<$<CONFIG:Release>:/fp:fast>
    )
    if({{ UPPER }}_USE_MARCH_NATIVE)
        target_compile_options({{cookiecutter.plugin_name}} PRIVATE
            $<$<CONFIG:Release>:/arch:AVX2>
        )
        message(STATUS "Target: MSVC x86_64 (AVX2)")
    else()
        # SSE2 is the default for MSVC x64, no flag needed for SSE4.2 baseline
        message(STATUS "Target: MSVC x86_64 (SSE2 baseline for distribution)")
    endif()
endif()

# Link JUCE modules
target_link_libraries({{cookiecutter.plugin_name}} PRIVATE
    juce::juce_audio_utils
    juce::juce_audio_processors
    juce::juce_graphics
    juce::juce_dsp
    {{cookiecutter.plugin_name}}Assets
PUBLIC
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
    juce::juce_recommended_warning_flags
)
