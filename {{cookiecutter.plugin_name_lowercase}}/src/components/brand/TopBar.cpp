#include "TopBar.h"
#include "BinaryData.h"

TopBar::TopBar() {
  {% if cookiecutter.include_advanced_ui == "yes" -%}
  auto configureButton = [this](juce::TextButton &button) {
    addAndMakeVisible(button);
    button.setClickingTogglesState(false);
    namespace C = {{cookiecutter.plugin_name}}Colors;
    button.setColour(juce::TextButton::buttonColourId,
                     juce::Colour(C::panelBg).brighter(0.06f));
    button.setColour(juce::TextButton::buttonOnColourId,
                     juce::Colour(C::accentWarm).withAlpha(0.22f));
    button.setColour(juce::TextButton::textColourOffId, juce::Colour(C::labelText));
    button.setColour(juce::TextButton::textColourOnId, juce::Colour(C::accentBright));
  };

  addAndMakeVisible(presetBox);
  presetBox.setComponentID("topbarPresetBox");
  presetBox.setTextWhenNothingSelected("Preset");
  presetBox.onChange = [this] {
    if (onPresetSelected)
      onPresetSelected(presetBox.getText());
  };

  configureButton(slotAButton);
  slotAButton.setComponentID("topbarABButton");
  configureButton(slotBButton);
  slotBButton.setComponentID("topbarABButton");
  configureButton(optionsButton);
  optionsButton.setComponentID("topbarABButton");

  slotAButton.onClick = [this] {
    if (onSelectSlotA)
      onSelectSlotA();
  };
  slotBButton.onClick = [this] {
    if (onSelectSlotB)
      onSelectSlotB();
  };
  optionsButton.onClick = [this] {
    if (onShowOptionsMenu)
      onShowOptionsMenu();
  };

  setActiveABSlot(true);
  {% endif -%}

  int logoDataSize = 0;
  const char *logoData = BinaryData::getNamedResource("logo_png", logoDataSize);
  if (logoData != nullptr && logoDataSize > 0) {
    logo = juce::ImageFileFormat::loadFrom(logoData, static_cast<size_t>(logoDataSize));
  }
}

{% if cookiecutter.include_advanced_ui == "yes" -%}
void TopBar::setActiveABSlot(bool isSlotA) {
  slotAButton.setToggleState(isSlotA, juce::dontSendNotification);
  slotBButton.setToggleState(!isSlotA, juce::dontSendNotification);
}

void TopBar::setPresetNames(const juce::StringArray &presetNames) {
  auto selectedText = presetBox.getText();
  presetBox.clear(juce::dontSendNotification);

  for (int i = 0; i < presetNames.size(); ++i)
    presetBox.addItem(presetNames[i], i + 1);

  if (selectedText.isNotEmpty())
    setSelectedPresetName(selectedText);
}

void TopBar::setSelectedPresetName(const juce::String &presetName) {
  for (int i = 0; i < presetBox.getNumItems(); ++i) {
    if (presetBox.getItemText(i) == presetName) {
      presetBox.setSelectedItemIndex(i, juce::dontSendNotification);
      return;
    }
  }

  presetBox.setText(presetName, juce::dontSendNotification);
}

juce::Component *TopBar::getOptionsTargetComponent() {
  return &optionsButton;
}
{% endif -%}

void TopBar::paint(juce::Graphics &g) {
  {% if cookiecutter.include_advanced_ui == "yes" -%}
  auto bounds = getLocalBounds().toFloat();

  juce::ColourGradient bg(juce::Colour({{cookiecutter.plugin_name}}Colors::topBarBg),
                          0.0f,
                          0.0f,
                          juce::Colour({{cookiecutter.plugin_name}}Colors::background),
                          bounds.getWidth(),
                          0.0f,
                          false);
  g.setGradientFill(bg);
  g.fillRect(bounds);
  {% else -%}
  g.fillAll(juce::Colour(0xff1a1a1a));
  {% endif -%}

  if (logo.isValid()) {
    const int logoHeight = getHeight() - 20;
    const int logoWidth = logo.getWidth() * logoHeight / logo.getHeight();
    const int logoX = 15;
    const int logoY = (getHeight() - logoHeight) / 2;
    g.drawImage(logo, logoX, logoY, logoWidth, logoHeight, 0, 0, logo.getWidth(),
                logo.getHeight());
  }

  {% if cookiecutter.include_advanced_ui == "yes" -%}
  g.setColour(juce::Colour({{cookiecutter.plugin_name}}Colors::accentWarm).withAlpha(0.4f));
  g.drawLine(0.0f, bounds.getBottom() - 1.0f, bounds.getWidth(), bounds.getBottom() - 1.0f, 1.0f);
  {% else -%}
  g.setColour(juce::Colour(0xff333333));
  g.drawLine(0, getHeight() - 1, getWidth(), getHeight() - 1, 1.0f);
  {% endif -%}
}

void TopBar::resized() {
  {% if cookiecutter.include_advanced_ui == "yes" -%}
  auto bounds = getLocalBounds().reduced(10, 7);
  auto rightArea = bounds.removeFromRight(266);

  auto positionControl = [](juce::Component &component, juce::Rectangle<int> &area, int width) {
    constexpr int controlHeight = 24;
    auto controlBounds = area.removeFromRight(width);
    controlBounds.setY(controlBounds.getY() + (controlBounds.getHeight() - controlHeight) / 2);
    controlBounds.setHeight(controlHeight);
    component.setBounds(controlBounds);
  };

  positionControl(optionsButton, rightArea, 34);
  rightArea.removeFromRight(4);
  positionControl(slotBButton, rightArea, 24);
  rightArea.removeFromRight(3);
  positionControl(slotAButton, rightArea, 24);
  rightArea.removeFromRight(6);
  positionControl(presetBox, rightArea, 135);
  {% else -%}
  // No controls in minimal mode
  {% endif -%}
}
