"""Tests for the JUCE cookiecutter template."""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml
from cookiecutter.main import cookiecutter  # type: ignore


@pytest.fixture
def template_dir():
    return Path(__file__).parent.parent.absolute()


@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def default_context():
    return {
        "plugin_name": "TestPlugin",
        "plugin_description": "A test JUCE audio plugin",
        "company_name": "TestCompany",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "juce_version": "7.0.12",
        "cpp_standard": "17",
        "include_vst2": "yes",
        "include_vst3": "yes",
        "include_au": "yes",
        "include_standalone": "yes",
        "include_clap": "yes",
        "include_faust": "no",
        "include_advanced_ui": "no",
        "include_ci": "yes",
    }


def generate(template_dir: Path, temp_output_dir: Path, context: dict[str, str]) -> Path:
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=context,
    )
    return Path(result)


def test_template_generates_successfully(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)
    assert project_dir.exists()
    assert project_dir.name == "testplugin"


def test_generated_core_files_exist(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)

    assert (project_dir / "CMakeLists.txt").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".gitignore").exists()
    assert (project_dir / "justfile").exists()
    assert (project_dir / "src" / "PluginProcessor.h").exists()
    assert (project_dir / "src" / "PluginProcessor.cpp").exists()
    assert (project_dir / "src" / "PluginEditor.h").exists()
    assert (project_dir / "src" / "PluginEditor.cpp").exists()
    assert (project_dir / "src" / "components" / "brand" / "TopBar.h").exists()
    assert (project_dir / "src" / "components" / "brand" / "TopBar.cpp").exists()
    assert (project_dir / "src" / "presets" / "PluginPresetManager.h").exists()
    assert (project_dir / "src" / "presets" / "PluginPresetManager.cpp").exists()
    assert (project_dir / "src" / "data" / "PluginParameters.h").exists()
    assert (project_dir / "src" / "data" / "RuntimeParameters.h").exists()


def test_plugin_name_substitution(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)

    cmake_content = (project_dir / "CMakeLists.txt").read_text()
    assert "project(TestPlugin" in cmake_content
    assert "juce_add_plugin(TestPlugin" in cmake_content
    assert 'COMPANY_NAME "TestCompany"' in cmake_content

    processor_h = (project_dir / "src" / "PluginProcessor.h").read_text()
    assert "class TestPluginAudioProcessor" in processor_h

    readme = (project_dir / "README.md").read_text()
    assert "# TestPlugin" in readme
    assert "TestCompany" in readme


def test_vst2_conditional(template_dir, temp_output_dir, default_context):
    with_vst2 = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "plugin_name": "WithVST2", "include_vst2": "yes"},
    )
    cmake_with = (with_vst2 / "CMakeLists.txt").read_text()
    assert "ENABLE_VST2" in cmake_with
    assert "juce_set_vst2_sdk_path" in cmake_with

    without_vst2 = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "plugin_name": "NoVST2", "include_vst2": "no"},
    )
    cmake_without = (without_vst2 / "CMakeLists.txt").read_text()
    assert "juce_set_vst2_sdk_path" not in cmake_without


def test_clap_conditional_enabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "plugin_name": "WithCLAP", "include_clap": "yes"},
    )
    cmake = (project_dir / "CMakeLists.txt").read_text()

    assert "WITHCLAP_ENABLE_CLAP" in cmake
    assert "clap_juce_extensions_plugin(TARGET WithCLAP" in cmake
    assert 'CLAP_ID "com.testcompany.withclap"' in cmake
    assert "CLAP_USE_JUCE_PARAMETER_RANGES ALL" in cmake

    # Pinned to a commit, never a tag: that repository's tags are CLAP spec versions
    # from 2022, and building against one silently yields a pre-CLAP-1.0 wrapper.
    assert re.search(r"WITHCLAP_CLAP_VERSION \"[0-9a-f]{40}\"", cmake)

    assert "plugin_enable_clap" in (project_dir / "justfile").read_text()
    assert "CLAP" in (project_dir / "README.md").read_text()


def test_clap_conditional_disabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        # Deliberately a name with no "clap" in it, so the negative assertions below
        # cannot be satisfied or defeated by the plugin name itself.
        {**default_context, "plugin_name": "PlainFx", "include_clap": "no"},
    )
    cmake = (project_dir / "CMakeLists.txt").read_text()

    assert "clap_juce_extensions_plugin" not in cmake
    assert "ENABLE_CLAP" not in cmake
    assert "clap-juce-extensions" not in cmake
    assert "plugin_enable_clap" not in (project_dir / "justfile").read_text()


def test_faust_conditional_enabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "yes", "include_advanced_ui": "yes"},
    )

    assert (project_dir / "dsp" / "testplugin.dsp").exists()
    assert (project_dir / "scripts" / "codegen.py").exists()
    assert (project_dir / "docs" / "faust-codegen.md").exists()

    processor_h = (project_dir / "src" / "PluginProcessor.h").read_text()
    assert '#include "FaustBridge.h"' in processor_h
    assert "FaustBridge faustBridge" in processor_h

    processor_cpp = (project_dir / "src" / "PluginProcessor.cpp").read_text()
    assert "faustBridge.prepare" in processor_cpp
    assert "faustBridge.process" in processor_cpp


def test_codegen_supports_max_sample_rate_flag(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "yes"},
    )
    codegen = (project_dir / "scripts" / "codegen.py").read_text()

    assert "--max-sample-rate" in codegen
    assert "rewrite_max_delay_constants_for_sample_rate" in codegen
    # Must not error out when the .dsp has no MAX_* constants (the starter .dsp
    # doesn't) -- this has to be a no-op, not a hard failure.
    assert "nothing to resize" in codegen


def test_daisy_conditional_enabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "yes", "include_daisy": "yes"},
    )

    assert (project_dir / "daisy" / "README.md").exists()
    assert (project_dir / "daisy" / "main.cpp").exists()
    assert (project_dir / "daisy" / "Makefile").exists()

    justfile = (project_dir / "justfile").read_text()
    assert "daisy-codegen" in justfile
    assert "daisy-build" in justfile
    assert "--max-sample-rate" in justfile

    gitignore = (project_dir / ".gitignore").read_text()
    assert "daisy/generated/" in gitignore
    assert "!daisy/Makefile" in gitignore

    docs = (project_dir / "docs" / "faust-codegen.md").read_text()
    assert "Daisy Seed scaffold" in docs

    main_cpp = (project_dir / "daisy" / "main.cpp").read_text()
    assert "TestPluginDSP DSY_SDRAM_BSS dsp;" in main_cpp
    assert "{{cookiecutter" not in main_cpp


def test_daisy_conditional_disabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "yes", "include_daisy": "no"},
    )

    assert not (project_dir / "daisy").exists()
    assert "daisy-codegen" not in (project_dir / "justfile").read_text()


def test_daisy_requires_faust(template_dir, temp_output_dir, default_context):
    """include_daisy=yes without include_faust=yes should warn and skip, not crash."""
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "no", "include_daisy": "yes"},
    )

    assert not (project_dir / "daisy").exists()
    assert "daisy-codegen" not in (project_dir / "justfile").read_text()


def test_faust_conditional_disabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_faust": "no", "include_advanced_ui": "yes"},
    )

    assert not (project_dir / "dsp").exists()
    assert not (project_dir / "scripts" / "codegen.py").exists()
    assert not (project_dir / "docs" / "faust-codegen.md").exists()

    processor_h = (project_dir / "src" / "PluginProcessor.h").read_text()
    assert "FaustBridge" not in processor_h

    runtime_header = (project_dir / "src" / "data" / "RuntimeParameters.h").read_text()
    assert "PluginParamIDs" in runtime_header


def test_advanced_ui_enabled_generates_ui_files(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_advanced_ui": "yes"},
    )

    assert (project_dir / "src" / "components" / "controls" / "RotaryKnob.h").exists()
    assert not (project_dir / "src" / "components" / "controls" / "FreezeButton.h").exists()
    assert (project_dir / "src" / "ui" / "TestPluginColors.h").exists()
    assert (project_dir / "src" / "ui" / "PluginLookAndFeel.h").exists()
    assert not (project_dir / "src" / "ui" / "ThemeTokens.h").exists()
    assert not (project_dir / "src" / "ui" / "ThemeTokens.cpp").exists()


def test_advanced_ui_disabled_strips_ui_files(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_advanced_ui": "no"},
    )

    assert not (project_dir / "src" / "components" / "controls" / "RotaryKnob.h").exists()
    assert not (project_dir / "src" / "components" / "controls" / "FreezeButton.h").exists()
    assert not (project_dir / "src" / "ui").exists()


def test_plugin_colors_namespace_is_templatized(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_advanced_ui": "yes"},
    )

    colors_h = (project_dir / "src" / "ui" / "TestPluginColors.h").read_text()
    assert "namespace TestPluginColors" in colors_h
    assert "background" in colors_h
    assert "topBarBg" in colors_h


def test_preset_paths_are_templatized(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)
    preset_cpp = (project_dir / "src" / "presets" / "PluginPresetManager.cpp").read_text()

    assert 'getChildFile("TestCompany")' in preset_cpp
    assert 'getChildFile("TestPlugin")' in preset_cpp
    assert '.testpluginpreset' in preset_cpp


def test_ci_conditional_enabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_ci": "yes"},
    )
    assert (project_dir / ".github" / "workflows" / "build.yml").exists()
    ci_content = (project_dir / ".github" / "workflows" / "build.yml").read_text()
    assert "workflow_dispatch" in ci_content
    assert "pluginval" in ci_content


def test_ci_conditional_disabled(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_ci": "no"},
    )
    assert not (project_dir / ".github").exists()


def test_ci_friendly_options_in_cmake(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)
    cmake_content = (project_dir / "CMakeLists.txt").read_text()
    assert "TESTPLUGIN_COPY_AFTER_BUILD" in cmake_content
    assert "TESTPLUGIN_USE_MARCH_NATIVE" in cmake_content
    assert "TESTPLUGIN_ENABLE_IPO" in cmake_content


def test_readme_mentions_advanced_ui_and_theming(template_dir, temp_output_dir, default_context):
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {**default_context, "include_advanced_ui": "yes"},
    )
    readme = (project_dir / "README.md").read_text()
    assert "advanced UI" in readme
    assert "theme" in readme.lower()
    assert "A/B" in readme


@pytest.mark.slow
def test_cmake_configures(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)
    build_dir = project_dir / "build"
    build_dir.mkdir()

    cmake_result = subprocess.run(
        ["cmake", "-B", str(build_dir), "-S", str(project_dir)],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )

    assert cmake_result.returncode == 0
    assert "CMake Error" not in cmake_result.stderr


def test_script_permissions(template_dir, temp_output_dir, default_context):
    project_dir = generate(template_dir, temp_output_dir, default_context)
    script_path = project_dir / "scripts" / "element_dev.sh"
    assert script_path.exists()
    assert script_path.read_text().startswith("#!/bin/bash")


@pytest.mark.parametrize("include_faust", ["yes", "no"])
def test_ci_yaml_is_valid(template_dir, temp_output_dir, default_context, include_faust):
    """Ensure the generated build.yml is valid YAML with correct indentation."""
    project_dir = generate(
        template_dir,
        temp_output_dir,
        {
            **default_context,
            "plugin_name": f"CITest{include_faust.title()}",
            "include_faust": include_faust,
            "include_ci": "yes",
        },
    )
    ci_path = project_dir / ".github" / "workflows" / "build.yml"
    assert ci_path.exists()

    # Must parse as valid YAML
    content = ci_path.read_text()
    workflow = yaml.safe_load(content)
    assert workflow is not None
    assert "jobs" in workflow

    # Every line inside the run: blocks must be properly indented
    # (no lines starting at column 0 inside a step's run block)
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            # Top-level keys (name, on, env, concurrency, jobs) are allowed at col 0
            if line == stripped and not any(
                stripped.startswith(k) for k in ("name:", "on:", "env:", "concurrency:", "jobs:")
            ):
                pytest.fail(
                    f"Line {line_no} has unexpected content at column 0: {line!r}"
                )
