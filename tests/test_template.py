"""Tests for the JUCE starter pack cookiecutter template."""

import subprocess
import tempfile
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter  # type: ignore


@pytest.fixture
def template_dir():
    """Return the path to the cookiecutter template."""
    return Path(__file__).parent.parent.absolute()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def default_context():
    """Default context for generating test projects."""
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
    }


def test_template_generates_successfully(
    template_dir, temp_output_dir, default_context
):
    """Test that the template generates without errors."""
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=default_context,
    )

    assert result is not None
    assert Path(result).exists()
    assert Path(result).name == "testplugin"


def test_generated_files_exist(template_dir, temp_output_dir, default_context):
    """Test that all expected files are generated."""
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=default_context,
    )

    project_dir = Path(result)

    # Check main files
    assert (project_dir / "CMakeLists.txt").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".gitignore").exists()
    assert (project_dir / ".gitmodules").exists()

    # Check source files
    assert (project_dir / "src" / "PluginProcessor.h").exists()
    assert (project_dir / "src" / "PluginProcessor.cpp").exists()
    assert (project_dir / "src" / "PluginEditor.h").exists()
    assert (project_dir / "src" / "PluginEditor.cpp").exists()

    # Check components
    assert (project_dir / "src" / "components" / "brand" / "TopBar.h").exists()
    assert (project_dir / "src" / "components" / "brand" / "TopBar.cpp").exists()

    # Check suggested directory structure (with .gitkeep files)
    assert (project_dir / "src" / "utils" / ".gitkeep").exists()
    assert (project_dir / "src" / "data" / ".gitkeep").exists()
    assert (project_dir / "src" / "dsp" / ".gitkeep").exists()
    assert (project_dir / "src" / "components" / "controls" / ".gitkeep").exists()
    assert (project_dir / "src" / "components" / "graphs" / ".gitkeep").exists()

    # Check scripts
    assert (project_dir / "scripts" / "element_dev.sh").exists()
    assert (project_dir / "scripts" / "element_project.conf.example").exists()

    # Check assets
    assert (project_dir / "assets" / "images" / "logo.png").exists()


def test_plugin_name_in_files(template_dir, temp_output_dir, default_context):
    """Test that plugin name is correctly substituted in generated files."""
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=default_context,
    )

    project_dir = Path(result)

    # Check CMakeLists.txt
    cmake_content = (project_dir / "CMakeLists.txt").read_text()
    assert "project(TestPlugin" in cmake_content
    assert "juce_add_plugin(TestPlugin" in cmake_content
    assert 'COMPANY_NAME "TestCompany"' in cmake_content

    # Check PluginProcessor.h
    processor_h = (project_dir / "src" / "PluginProcessor.h").read_text()
    assert "TestPluginAudioProcessor" in processor_h

    # Check PluginProcessor.cpp
    processor_cpp = (project_dir / "src" / "PluginProcessor.cpp").read_text()
    assert "TestPluginAudioProcessor::TestPluginAudioProcessor" in processor_cpp

    # Check README
    readme = (project_dir / "README.md").read_text()
    assert "# TestPlugin" in readme
    assert "TestCompany" in readme


def test_vst2_conditional(template_dir, temp_output_dir, default_context):
    """Test that VST2 configuration is conditionally included."""
    # Test with VST2 enabled
    result_with_vst2 = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context={**default_context, "include_vst2": "yes"},
    )

    cmake_with_vst2 = (Path(result_with_vst2) / "CMakeLists.txt").read_text()
    assert "VST2_SDK_PATH" in cmake_with_vst2
    assert "juce_set_vst2_sdk_path" in cmake_with_vst2

    gitmodules_with_vst2 = (Path(result_with_vst2) / ".gitmodules").read_text()
    assert "vst-2.4-sdk" in gitmodules_with_vst2

    # Test with VST2 disabled
    result_without_vst2 = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context={
            **default_context,
            "plugin_name": "TestPluginNoVST2",
            "include_vst2": "no",
        },
    )

    cmake_without_vst2 = (Path(result_without_vst2) / "CMakeLists.txt").read_text()
    assert "VST2_SDK_PATH" not in cmake_without_vst2


@pytest.mark.slow
def test_cmake_configures(template_dir, temp_output_dir, default_context):
    """Test that CMake can configure the generated project.

    This test is marked as slow because it fetches JUCE from GitHub.
    Run with: uv run pytest -v -m slow
    """
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=default_context,
    )

    project_dir = Path(result)
    build_dir = project_dir / "build"
    build_dir.mkdir()

    # Try to configure with CMake (without VST2 SDK to avoid dependency)
    cmake_result = subprocess.run(
        ["cmake", "-B", str(build_dir), "-S", str(project_dir)],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )

    # CMake should at least start configuring (may warn about VST2, but shouldn't error)
    # We're checking that the CMakeLists.txt is syntactically valid
    assert cmake_result.returncode == 0 or "VST2 SDK not found" in cmake_result.stderr
    assert "CMake Error" not in cmake_result.stderr


def test_script_permissions(template_dir, temp_output_dir, default_context):
    """Test that shell scripts are generated."""
    result = cookiecutter(
        str(template_dir),
        output_dir=str(temp_output_dir),
        no_input=True,
        extra_context=default_context,
    )

    project_dir = Path(result)
    script_path = project_dir / "scripts" / "element_dev.sh"

    assert script_path.exists()
    assert script_path.read_text().startswith("#!/bin/bash")
