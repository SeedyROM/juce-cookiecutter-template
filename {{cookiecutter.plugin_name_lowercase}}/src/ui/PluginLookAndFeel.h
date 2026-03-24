#pragma once

#include "{{cookiecutter.plugin_name}}Colors.h"

#include <juce_gui_basics/juce_gui_basics.h>

class PluginLookAndFeel : public juce::LookAndFeel_V4 {
public:
  PluginLookAndFeel();
  ~PluginLookAndFeel() override = default;

  void drawRotarySlider(juce::Graphics &g,
                        int x,
                        int y,
                        int width,
                        int height,
                        float sliderPosProportional,
                        float rotaryStartAngle,
                        float rotaryEndAngle,
                        juce::Slider &slider) override;

  void drawToggleButton(juce::Graphics &g,
                        juce::ToggleButton &button,
                        bool shouldDrawButtonAsHighlighted,
                        bool shouldDrawButtonAsDown) override;

  void drawLabel(juce::Graphics &g, juce::Label &label) override;
  juce::Label *createSliderTextBox(juce::Slider &slider) override;
  juce::Slider::SliderLayout getSliderLayout(juce::Slider &slider) override;

  void drawButtonBackground(juce::Graphics &g,
                            juce::Button &button,
                            const juce::Colour &backgroundColour,
                            bool shouldDrawButtonAsHighlighted,
                            bool shouldDrawButtonAsDown) override;
  void drawButtonText(juce::Graphics &g,
                      juce::TextButton &button,
                      bool shouldDrawButtonAsHighlighted,
                      bool shouldDrawButtonAsDown) override;
  void drawComboBox(juce::Graphics &g,
                    int width,
                    int height,
                    bool isButtonDown,
                    int buttonX,
                    int buttonY,
                    int buttonW,
                    int buttonH,
                    juce::ComboBox &box) override;
  juce::Font getTextButtonFont(juce::TextButton &button, int buttonHeight) override;
  juce::Font getComboBoxFont(juce::ComboBox &box) override;

private:
  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PluginLookAndFeel)
};
