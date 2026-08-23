{% set UPPER = cookiecutter.plugin_name | upper -%}
cmake_minimum_required(VERSION 3.22)

project({{cookiecutter.plugin_name}} VERSION 0.1.0)

include(CheckIPOSupported)

set(CMAKE_SUPPRESS_DEVELOPER_WARNINGS ON CACHE INTERNAL "")

set(CMAKE_CXX_STANDARD {{cookiecutter.cpp_standard}})
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option({{ UPPER }}_COPY_AFTER_BUILD "Copy plugin to system dirs after build" ON)
option({{ UPPER }}_USE_MARCH_NATIVE "Use -march=native (disable for distributable builds)" ON)
option({{ UPPER }}_ENABLE_IPO "Enable interprocedural optimization/LTO in Release" ON)
{% if cookiecutter.include_faust == "yes" -%}
option({{ UPPER }}_ENABLE_CODEGEN "Run Faust codegen (requires faust on PATH)" ON)
{% endif -%}
{% if cookiecutter.include_vst2 == "yes" -%}
option({{ UPPER }}_ENABLE_VST2 "Enable legacy VST2 builds when SDK is available" OFF)
{% endif -%}
{% if cookiecutter.include_clap == "yes" -%}
# CLAP is not a JUCE format, so it lives outside {{ UPPER }}_FORMATS and gets its own
# switch. Off skips the fetch entirely, for builds without network access.
option({{ UPPER }}_ENABLE_CLAP "Build a CLAP via clap-juce-extensions" ON)

# A commit, not a tag. That repository's tags ("0.26.0" and friends) are CLAP *spec*
# versions from 2022 rather than releases of the extension, and building against one
# silently gets a pre-CLAP-1.0 wrapper whose CMake signature is different enough that
# arguments land in the wrong parameters and emerge as mangled preprocessor defines.
# Upstream ships from main, so a pinned commit is how a reproducible build works here.
set({{ UPPER }}_CLAP_VERSION "c1a5ad025f95d01e03267857fa8276ebeed16500"
    CACHE STRING "clap-juce-extensions commit to build against")
{% endif -%}
set({{ UPPER }}_FORMATS "{% if cookiecutter.include_vst2 == "yes" %}VST {% endif %}{% if cookiecutter.include_vst3 == "yes" %}VST3 {% endif %}{% if cookiecutter.include_au == "yes" %}AU {% endif %}{% if cookiecutter.include_standalone == "yes" %}Standalone{% endif %}" CACHE STRING "Space-separated list of plugin formats to build")

{% if cookiecutter.include_vst2 == "yes" -%}
if({{ UPPER }}_ENABLE_VST2)
    set(VST2_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/external/vst-2.4-sdk/vstsdk2.4" CACHE PATH "Path to VST2 SDK")
    if(EXISTS "${VST2_SDK_PATH}/pluginterfaces/vst2.x/aeffect.h")
        message(STATUS "VST2 SDK found at: ${VST2_SDK_PATH}")
    else()
        message(FATAL_ERROR "{{ UPPER }}_ENABLE_VST2=ON but VST2 SDK not found at: ${VST2_SDK_PATH}")
    endif()
endif()
{% endif -%}

include(FetchContent)
FetchContent_Declare(
    JUCE
    URL https://github.com/juce-framework/JUCE/archive/refs/tags/{{cookiecutter.juce_version}}.tar.gz
)
FetchContent_MakeAvailable(JUCE)

{% if cookiecutter.include_vst2 == "yes" -%}
if({{ UPPER }}_ENABLE_VST2)
    juce_set_vst2_sdk_path("${VST2_SDK_PATH}")
endif()
{% endif -%}

{% if cookiecutter.include_faust == "yes" -%}
set(FAUST_GEN_DIR "${CMAKE_SOURCE_DIR}/src/dsp/generated")

if({{ UPPER }}_ENABLE_CODEGEN)
    find_program(FAUST_EXECUTABLE faust)
    if(FAUST_EXECUTABLE)
        message(STATUS "Faust found: ${FAUST_EXECUTABLE} - codegen enabled")

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
        message(STATUS "Faust not found - codegen disabled, using committed generated files")
    endif()
else()
    message(STATUS "Faust codegen disabled ({{ UPPER }}_ENABLE_CODEGEN=OFF)")
endif()
{% endif -%}

{% if cookiecutter.include_clap == "yes" -%}
# After JUCE on purpose: the extension's CMake reads CMAKE_CXX_STANDARD and expects the
# JUCE targets to exist already. It pulls the CLAP headers and helpers in as git
# submodules, which FetchContent handles on its own.
if({{ UPPER }}_ENABLE_CLAP)
    FetchContent_Declare(
        clap-juce-extensions
        GIT_REPOSITORY https://github.com/free-audio/clap-juce-extensions.git
        GIT_TAG ${{"{"}}{{ UPPER }}_CLAP_VERSION}
    )
    FetchContent_MakeAvailable(clap-juce-extensions)
endif()

{% endif -%}
separate_arguments({{ UPPER }}_FORMATS_LIST UNIX_COMMAND "${{"{"}}{{ UPPER }}_FORMATS}")

{% if cookiecutter.include_vst2 == "yes" -%}
if(NOT {{ UPPER }}_ENABLE_VST2)
    list(REMOVE_ITEM {{ UPPER }}_FORMATS_LIST VST)
endif()
{% endif -%}

list(REMOVE_DUPLICATES {{ UPPER }}_FORMATS_LIST)

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
if(TARGET faust_codegen)
    add_dependencies({{cookiecutter.plugin_name}} faust_codegen)
endif()
{% endif -%}

if({{ UPPER }}_ENABLE_IPO)
    check_ipo_supported(RESULT PLUGIN_IPO_SUPPORTED OUTPUT PLUGIN_IPO_ERROR)
    if(PLUGIN_IPO_SUPPORTED)
        set_property(TARGET {{cookiecutter.plugin_name}} PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
        message(STATUS "IPO/LTO enabled for Release builds")
    else()
        message(STATUS "IPO/LTO unavailable: ${PLUGIN_IPO_ERROR}")
    endif()
endif()

juce_add_binary_data({{cookiecutter.plugin_name}}Assets SOURCES
    assets/images/logo.png
)

target_sources({{cookiecutter.plugin_name}} PRIVATE
    src/PluginProcessor.cpp
    src/PluginEditor.cpp
    src/components/brand/TopBar.cpp
    src/presets/PluginPresetManager.cpp
    {% if cookiecutter.include_advanced_ui == "yes" -%}
    src/components/controls/RotaryKnob.cpp
    src/ui/PluginLookAndFeel.cpp
    {% endif -%}
)

target_include_directories({{cookiecutter.plugin_name}} PRIVATE
    {% if cookiecutter.include_faust == "yes" -%}
    ${FAUST_GEN_DIR}
    {% endif -%}
    ${CMAKE_SOURCE_DIR}/src
)

target_compile_definitions({{cookiecutter.plugin_name}} PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options({{cookiecutter.plugin_name}} PRIVATE
        $<$<CONFIG:Release>:-O3>
        $<$<CONFIG:Release>:-ffast-math>
        $<$<CONFIG:Release>:-ffp-contract=fast>
        $<$<CONFIG:Release>:-fno-math-errno>
        $<$<CONFIG:Release>:-funroll-loops>
    )

    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
        if({{ UPPER }}_USE_MARCH_NATIVE)
            target_compile_options({{cookiecutter.plugin_name}} PRIVATE
                $<$<CONFIG:Release>:-march=native>
            )
            message(STATUS "Target: x86_64 (using -march=native for AVX2/FMA)")
        else()
            target_compile_options({{cookiecutter.plugin_name}} PRIVATE
                $<$<CONFIG:Release>:-msse4.2>
            )
            message(STATUS "Target: x86_64 (using SSE4.2 baseline for distribution)")
        endif()
    endif()

    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        target_compile_options({{cookiecutter.plugin_name}} PRIVATE
            $<$<CONFIG:Release>:-fdenormal-fp-math=positive-zero>
        )
    endif()
elseif(MSVC)
    target_compile_options({{cookiecutter.plugin_name}} PRIVATE
        $<$<CONFIG:Release>:/O2>
        $<$<CONFIG:Release>:/fp:fast>
        $<$<CONFIG:Release>:/Oi>
        $<$<CONFIG:Release>:/Gy>
        $<$<CONFIG:Release>:/Gw>
    )
    if({{ UPPER }}_USE_MARCH_NATIVE)
        target_compile_options({{cookiecutter.plugin_name}} PRIVATE
            $<$<CONFIG:Release>:/arch:AVX2>
        )
    endif()
endif()

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

{% if cookiecutter.include_clap == "yes" -%}
if({{ UPPER }}_ENABLE_CLAP)
    # Creates the {{cookiecutter.plugin_name}}_CLAP target alongside the JUCE format
    # targets, and picks up COPY_PLUGIN_AFTER_BUILD from the JUCE target on its own.
    #
    # CLAP_USE_JUCE_PARAMETER_RANGES ALL: without it a host sees every parameter as 0-1
    # and shows "0.41" where the plugin means "-4.3 dB". This is baked into how
    # automation gets stored, so it is a decision worth making before anyone has a
    # session to break.
    #
    # Known gap: clap-juce-extensions does not map JUCE's getBypassParameter() onto
    # CLAP_PARAM_IS_BYPASS, so a CLAP host's own bypass button is not bound to the
    # plugin's bypass parameter. VST3 and AU are unaffected.
    clap_juce_extensions_plugin(TARGET {{cookiecutter.plugin_name}}
        CLAP_ID "com.{{cookiecutter.company_name_lowercase}}.{{cookiecutter.plugin_name_lowercase}}"
        CLAP_FEATURES audio-effect utility
        CLAP_USE_JUCE_PARAMETER_RANGES ALL
    )
endif()
{% endif -%}
