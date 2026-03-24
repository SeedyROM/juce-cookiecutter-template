#include "PluginEditor.h"
#include "BinaryData.h"
#include "PluginProcessor.h"

{% if cookiecutter.include_advanced_ui == "yes" -%}
#include "ui/{{cookiecutter.plugin_name}}Colors.h"

#include <memory>
{% endif -%}

{{cookiecutter.plugin_name}}AudioProcessorEditor::{{cookiecutter.plugin_name}}AudioProcessorEditor(
    {{cookiecutter.plugin_name}}AudioProcessor &p)
    : AudioProcessorEditor(&p), audioProcessor(p) {
{% if cookiecutter.include_advanced_ui == "yes" -%}
  setLookAndFeel(&pluginLnf);
{% endif -%}

  addAndMakeVisible(topBar);

{% if cookiecutter.include_advanced_ui == "yes" -%}
  topBar.onSelectSlotA = [this] {
    audioProcessor.setActiveABSlot({{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A);
    topBar.setActiveABSlot(true);
    refreshPresetControls();
  };
  topBar.onSelectSlotB = [this] {
    audioProcessor.setActiveABSlot({{cookiecutter.plugin_name}}AudioProcessor::ABSlot::B);
    topBar.setActiveABSlot(false);
    refreshPresetControls();
  };
  topBar.onPresetSelected = [this](const juce::String &presetName) {
    if (audioProcessor.loadPreset(presetName))
      refreshPresetControls();
  };
  topBar.onShowOptionsMenu = [this] { showOptionsMenu(); };
  topBar.setActiveABSlot(audioProcessor.getActiveABSlot() == {{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A);
  refreshPresetControls();

  setResizable(true, true);
  setResizeLimits(minEditorWidth, minEditorHeight, 1072, 644);
  setSize(minEditorWidth, minEditorHeight);

  startTimerHz(24);
{% else -%}
  setSize(800, 600);
{% endif -%}
}

{{cookiecutter.plugin_name}}AudioProcessorEditor::~{{cookiecutter.plugin_name}}AudioProcessorEditor() {
{% if cookiecutter.include_advanced_ui == "yes" -%}
  stopTimer();
  setLookAndFeel(nullptr);
{% endif -%}
}

{% if cookiecutter.include_advanced_ui == "yes" -%}
void {{cookiecutter.plugin_name}}AudioProcessorEditor::timerCallback() {
  // Refresh metered knobs here at ~24 Hz. For example:
  //   myKnob.refreshMeter();
  // To wire a knob to a meter source, call in the constructor:
  //   myKnob.setMeterSource([&p] { return p.getOutputMeterPeak(); });
}

void {{cookiecutter.plugin_name}}AudioProcessorEditor::refreshPresetControls() {
  topBar.setPresetNames(audioProcessor.getAvailablePresetNames());
  topBar.setSelectedPresetName(audioProcessor.getDisplayedPresetName());
  topBar.setActiveABSlot(audioProcessor.getActiveABSlot() == {{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A);
}

void {{cookiecutter.plugin_name}}AudioProcessorEditor::promptSavePreset() {
  auto dialog = std::make_unique<juce::AlertWindow>(
      "Save Preset", "Enter a preset name.", juce::AlertWindow::NoIcon);
  dialog->addTextEditor("presetName", audioProcessor.getActivePresetName(), "Preset name");
  dialog->addButton("Save", 1);
  dialog->addButton("Cancel", 0);

  auto *dialogPtr = dialog.release();
  dialogPtr->enterModalState(
      true,
      juce::ModalCallbackFunction::create([this, dialogPtr](int result) {
        std::unique_ptr<juce::AlertWindow> owner(dialogPtr);
        if (result == 1 &&
            audioProcessor.saveUserPreset(dialogPtr->getTextEditorContents("presetName").trim()))
          refreshPresetControls();
      }),
      true);
}

void {{cookiecutter.plugin_name}}AudioProcessorEditor::showOptionsMenu() {
  juce::PopupMenu menu;
  menu.setLookAndFeel(&pluginLnf);
  menu.addItem(1, "Copy A to B");
  menu.addItem(2, "Copy B to A");
  menu.addItem(3, "Clear A/B", audioProcessor.hasDistinctABState());
  menu.addSeparator();
  menu.addItem(4, "Save Preset...");
  menu.addItem(5,
               "Delete Current Preset",
               !audioProcessor.getActivePresetName().isEmpty() &&
                   !audioProcessor.isActivePresetFactory());
  menu.addItem(6, "Reveal Presets Folder");

  menu.showMenuAsync(
      juce::PopupMenu::Options().withTargetComponent(topBar.getOptionsTargetComponent()),
      [this](int result) {
        if (result == 1)
          audioProcessor.copyABSlot({{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A,
                                    {{cookiecutter.plugin_name}}AudioProcessor::ABSlot::B);
        else if (result == 2)
          audioProcessor.copyABSlot({{cookiecutter.plugin_name}}AudioProcessor::ABSlot::B,
                                    {{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A);
        else if (result == 3)
          audioProcessor.clearABState();
        else if (result == 4)
          promptSavePreset();
        else if (result == 5)
          audioProcessor.deleteActiveUserPreset();
        else if (result == 6)
          audioProcessor.revealPresetDirectory();

        topBar.setActiveABSlot(audioProcessor.getActiveABSlot() ==
                               {{cookiecutter.plugin_name}}AudioProcessor::ABSlot::A);
        refreshPresetControls();
      });
}
{% endif -%}

void {{cookiecutter.plugin_name}}AudioProcessorEditor::paint(juce::Graphics &g) {
{% if cookiecutter.include_advanced_ui == "yes" -%}
  g.fillAll(juce::Colour({{cookiecutter.plugin_name}}Colors::background));
{% else -%}
  g.fillAll(juce::Colour(0xff1a1a1a));
{% endif -%}
}

void {{cookiecutter.plugin_name}}AudioProcessorEditor::resized() {
  auto bounds = getLocalBounds();
  topBar.setBounds(bounds.removeFromTop(50));

{% if cookiecutter.include_advanced_ui != "yes" -%}
  bounds.reduce(10, 10);
{% endif -%}
}
