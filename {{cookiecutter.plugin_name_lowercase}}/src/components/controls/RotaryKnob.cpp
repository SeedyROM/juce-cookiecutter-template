#include "RotaryKnob.h"

#include <cmath>

namespace {

juce::Label *findSliderValueLabel(juce::Slider &slider) {
  for (int i = 0; i < slider.getNumChildComponents(); ++i)
    if (auto *label = dynamic_cast<juce::Label *>(slider.getChildComponent(i)))
      return label;

  return nullptr;
}

} // namespace

RotaryKnob::RotaryKnob(juce::AudioProcessorValueTreeState &apvts,
                       const juce::String &paramID,
                       const juce::String &labelText,
                       const juce::String &suffix,
                       bool showAsPercentage) {
  slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
  slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 68, 22);
  slider.setColour(juce::Slider::textBoxTextColourId, juce::Colour({{cookiecutter.plugin_name}}Colors::valueText));
  slider.setColour(juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
  slider.setColour(juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
  slider.getProperties().set("pluginShowMeter", false);

  slider.onValueChange = [this] { refreshMeter(); };

  addAndMakeVisible(slider);

  label.setText(labelText, juce::dontSendNotification);
  label.setJustificationType(juce::Justification::centred);
  label.setColour(juce::Label::textColourId, juce::Colour({{cookiecutter.plugin_name}}Colors::labelText));
  label.setFont(juce::Font(12.0f, juce::Font::bold));
  addAndMakeVisible(label);

  attachment =
      std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(apvts, paramID, slider);

  valueLabel = findSliderValueLabel(slider);

  if (showAsPercentage) {
    slider.textFromValueFunction = [suffix](double value) {
      return juce::String(juce::roundToInt(value * 100.0)) + suffix;
    };
    slider.valueFromTextFunction = [suffix](const juce::String &text) {
      auto stripped = text.trimCharactersAtEnd(suffix);
      return stripped.getDoubleValue() / 100.0;
    };
  } else if (suffix.isNotEmpty()) {
    auto existingTextFromValue = slider.textFromValueFunction;
    slider.textFromValueFunction = [existingTextFromValue, suffix](double value) {
      if (suffix == " Hz" && value >= 1000.0) {
        const auto truncatedKhz = std::floor(value / 10.0) / 100.0;
        return juce::String(truncatedKhz, 2) + " kHz";
      }

      if (existingTextFromValue)
        return existingTextFromValue(value) + suffix;
      return juce::String(value) + suffix;
    };
    slider.valueFromTextFunction = [suffix](const juce::String &text) {
      auto trimmed = text.trim();
      if (suffix == " Hz" && trimmed.endsWithIgnoreCase("kHz"))
        return trimmed.upToLastOccurrenceOf("k", false, false).trim().getDoubleValue() * 1000.0;

      auto stripped = trimmed.trimCharactersAtEnd(suffix);
      return stripped.getDoubleValue();
    };
  }

  slider.updateText();
  refreshMeter();
}

void RotaryKnob::setMeterSource(std::function<float()> newMeterSource,
                                bool shouldMeterColourValueText) {
  meterSource = std::move(newMeterSource);
  meterColourValueText = shouldMeterColourValueText;
  slider.getProperties().set("pluginShowMeter", meterSource != nullptr);
  refreshMeter();
}

void RotaryKnob::refreshMeter() {
  meterPeak = meterSource ? meterSource() : 0.0f;

  slider.getProperties().set("pluginMeterPeak", meterPeak);

  if (valueLabel != nullptr) {
    const auto useActiveMeterColour = meterColourValueText && meterPeak > 1.0e-4f;
    valueLabel->setColour(juce::Label::textColourId,
                          useActiveMeterColour
                               ? {{cookiecutter.plugin_name}}Colors::meterColourForPeak(meterPeak)
                               : juce::Colour({{cookiecutter.plugin_name}}Colors::valueText));
    valueLabel->repaint();
  }

  slider.repaint();
}

void RotaryKnob::resized() {
  auto bounds = getLocalBounds();
  label.setBounds(bounds.removeFromTop(18));
  bounds.removeFromBottom(2);
  slider.setBounds(bounds);
  valueLabel = findSliderValueLabel(slider);
  refreshMeter();
}
