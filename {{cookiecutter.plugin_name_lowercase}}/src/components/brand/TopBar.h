#pragma once

#include <functional>

{% if cookiecutter.include_advanced_ui == "yes" -%}
#include "ui/{{cookiecutter.plugin_name}}Colors.h"
{% endif -%}

#include <juce_gui_basics/juce_gui_basics.h>

class TopBar : public juce::Component {
public:
  TopBar();
  ~TopBar() override = default;

  void paint(juce::Graphics &g) override;
  void resized() override;

{% if cookiecutter.include_advanced_ui == "yes" -%}
  void setActiveABSlot(bool isSlotA);
  void setPresetNames(const juce::StringArray &presetNames);
  void setSelectedPresetName(const juce::String &presetName);
  juce::Component *getOptionsTargetComponent();

  std::function<void()> onSelectSlotA;
  std::function<void()> onSelectSlotB;
  std::function<void(const juce::String &presetName)> onPresetSelected;
  std::function<void()> onShowOptionsMenu;
{% endif -%}

private:
  juce::Image logo;

{% if cookiecutter.include_advanced_ui == "yes" -%}
  juce::ComboBox presetBox;
  juce::TextButton slotAButton{"A"};
  juce::TextButton slotBButton{"B"};
  juce::TextButton optionsButton{"..."};
{% endif -%}

  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(TopBar)
};
