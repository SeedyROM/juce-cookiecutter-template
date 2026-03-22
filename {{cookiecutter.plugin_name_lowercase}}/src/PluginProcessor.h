#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_dsp/juce_dsp.h>

{% if cookiecutter.include_faust == "yes" -%}
#include "FaustBridge.h"

{% endif -%}
class {{cookiecutter.plugin_name}}AudioProcessor : public juce::AudioProcessor {
public:
  {{cookiecutter.plugin_name}}AudioProcessor();
  ~{{cookiecutter.plugin_name}}AudioProcessor() override;

  void prepareToPlay(double sampleRate, int samplesPerBlock) override;
  void releaseResources() override;

  bool isBusesLayoutSupported(const BusesLayout &layouts) const override;

  void processBlock(juce::AudioBuffer<float> &, juce::MidiBuffer &) override;

  juce::AudioProcessorEditor *createEditor() override;
  bool hasEditor() const override;

  const juce::String getName() const override;

  bool acceptsMidi() const override;
  bool producesMidi() const override;
  bool isMidiEffect() const override;
  double getTailLengthSeconds() const override;

  int getNumPrograms() override;
  int getCurrentProgram() override;
  void setCurrentProgram(int index) override;
  const juce::String getProgramName(int index) override;
  void changeProgramName(int index, const juce::String &newName) override;

  void getStateInformation(juce::MemoryBlock &destData) override;
  void setStateInformation(const void *data, int sizeInBytes) override;

{% if cookiecutter.include_faust == "yes" -%}
  // Public access to APVTS for the editor
  juce::AudioProcessorValueTreeState apvts;

  // Public access to the bridge for the editor (e.g. for reading param values)
  FaustBridge &getFaustBridge() { return faustBridge; }

{% endif -%}
private:
{% if cookiecutter.include_faust == "yes" -%}
  FaustBridge faustBridge;

{% endif -%}
  JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR({{cookiecutter.plugin_name}}AudioProcessor)
};
