#pragma once

#include "ui/{{cookiecutter.plugin_name}}Colors.h"
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <functional>

class RotaryKnob : public juce::Component {
public:
  RotaryKnob(juce::AudioProcessorValueTreeState &apvts,
             const juce::String &paramID,
             const juce::String &labelText,
             const juce::String &suffix = "",
             bool showAsPercentage = false);
  ~RotaryKnob() override = default;

  void resized() override;
  void setMeterSource(std::function<float()> meterSource, bool meterColourValueText = true);
  void refreshMeter();

  juce::Slider &getSlider() { return slider; }

private:
  juce::Slider slider;
  juce::Label label;
  juce::Label *valueLabel = nullptr;
  std::function<float()> meterSource;
  float meterPeak = 0.0f;
  bool meterColourValueText = false;
  std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;

  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(RotaryKnob)
};
