#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

namespace PluginParamIDs {
// Define your parameter IDs here, e.g.:
// inline constexpr const char* mix = "mix";
// inline constexpr const char* gain = "gain";
} // namespace PluginParamIDs

namespace PluginParameters {

inline juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
  std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

  // Add your parameters here, e.g.:
  // params.push_back(std::make_unique<juce::AudioParameterFloat>(
  {% raw %}//     juce::ParameterID{PluginParamIDs::mix, 1}, "Mix",{% endraw %}
  //     juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));

  return {params.begin(), params.end()};
}

} // namespace PluginParameters
