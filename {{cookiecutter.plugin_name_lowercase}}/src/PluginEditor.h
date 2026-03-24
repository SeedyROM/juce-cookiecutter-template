#pragma once

#include "PluginProcessor.h"
#include "components/brand/TopBar.h"

{% if cookiecutter.include_advanced_ui == "yes" -%}
#include "ui/PluginLookAndFeel.h"
{% endif -%}

#include <juce_audio_processors/juce_audio_processors.h>

class {{cookiecutter.plugin_name}}AudioProcessorEditor : public juce::AudioProcessorEditor
{% if cookiecutter.include_advanced_ui == "yes" -%}
    , private juce::Timer
{% endif -%}
{
public:
  {{cookiecutter.plugin_name}}AudioProcessorEditor({{cookiecutter.plugin_name}}AudioProcessor &);
  ~{{cookiecutter.plugin_name}}AudioProcessorEditor() override;

  void paint(juce::Graphics &) override;
  void resized() override;

private:
{% if cookiecutter.include_advanced_ui == "yes" -%}
  void timerCallback() override;
  void showOptionsMenu();
  void promptSavePreset();
  void refreshPresetControls();

  static constexpr int minEditorWidth = 760;
  static constexpr int minEditorHeight = 520;
{% endif -%}

  {{cookiecutter.plugin_name}}AudioProcessor &audioProcessor;

{% if cookiecutter.include_advanced_ui == "yes" -%}
  PluginLookAndFeel pluginLnf;
{% endif -%}

  TopBar topBar;

  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR({{cookiecutter.plugin_name}}AudioProcessorEditor)
};
