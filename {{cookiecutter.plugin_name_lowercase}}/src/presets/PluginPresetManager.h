#pragma once

#include <juce_data_structures/juce_data_structures.h>

#include <vector>

class PluginPresetManager {
public:
  struct PresetInfo {
    juce::String name;
    bool isFactory = false;
    juce::File file;
    juce::ValueTree state;
  };

  static std::vector<PresetInfo> getAvailablePresets(const juce::ValueTree& referenceState,
                                                     const juce::Identifier& pluginStateType);

  static juce::ValueTree loadPresetState(const juce::String& presetName,
                                         const juce::ValueTree& referenceState,
                                         const juce::Identifier& pluginStateType);

  static bool saveUserPreset(const juce::String& presetName, const juce::ValueTree& wrappedState);
  static bool deleteUserPreset(const juce::String& presetName);
  static void revealPresetDirectory();
  static bool isFactoryPreset(const juce::String& presetName,
                              const juce::ValueTree& referenceState,
                              const juce::Identifier& pluginStateType);

private:
  static juce::File getPresetDirectory();

  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PluginPresetManager)
};
