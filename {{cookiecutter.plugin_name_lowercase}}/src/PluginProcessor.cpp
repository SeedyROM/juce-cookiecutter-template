#include "PluginProcessor.h"
#include "PluginEditor.h"

{{cookiecutter.plugin_name}}AudioProcessor::{{cookiecutter.plugin_name}}AudioProcessor()
    : AudioProcessor(
          BusesProperties()
              .withInput("Input", juce::AudioChannelSet::stereo(), true)
{% if cookiecutter.include_faust == "yes" -%}
              .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      apvts(*this, nullptr, "Parameters", FaustParams::createLayout()),
      faustBridge(apvts) {}
{% else -%}
              .withOutput("Output", juce::AudioChannelSet::stereo(), true)) {}
{% endif %}
{{cookiecutter.plugin_name}}AudioProcessor::~{{cookiecutter.plugin_name}}AudioProcessor() {}

const juce::String {{cookiecutter.plugin_name}}AudioProcessor::getName() const {
  return JucePlugin_Name;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::acceptsMidi() const { return false; }

bool {{cookiecutter.plugin_name}}AudioProcessor::producesMidi() const { return false; }

bool {{cookiecutter.plugin_name}}AudioProcessor::isMidiEffect() const { return false; }

double {{cookiecutter.plugin_name}}AudioProcessor::getTailLengthSeconds() const { return 0.0; }

int {{cookiecutter.plugin_name}}AudioProcessor::getNumPrograms() { return 1; }

int {{cookiecutter.plugin_name}}AudioProcessor::getCurrentProgram() { return 0; }

void {{cookiecutter.plugin_name}}AudioProcessor::setCurrentProgram(int index) {
  juce::ignoreUnused(index);
}

const juce::String {{cookiecutter.plugin_name}}AudioProcessor::getProgramName(int index) {
  juce::ignoreUnused(index);
  return {};
}

void {{cookiecutter.plugin_name}}AudioProcessor::changeProgramName(int index,
                                              const juce::String &newName) {
  juce::ignoreUnused(index, newName);
}

void {{cookiecutter.plugin_name}}AudioProcessor::prepareToPlay(double sampleRate,
                                          int samplesPerBlock) {
{% if cookiecutter.include_faust == "yes" -%}
  faustBridge.prepare(sampleRate, samplesPerBlock);
{% else -%}
  juce::ignoreUnused(sampleRate, samplesPerBlock);

  // Initialize your DSP here
{% endif -%}
}

void {{cookiecutter.plugin_name}}AudioProcessor::releaseResources() {
  // Release resources here
}

bool {{cookiecutter.plugin_name}}AudioProcessor::isBusesLayoutSupported(
    const BusesLayout &layouts) const {
  if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::mono() &&
      layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo())
    return false;

  if (layouts.getMainOutputChannelSet() != layouts.getMainInputChannelSet())
    return false;

  return true;
}

void {{cookiecutter.plugin_name}}AudioProcessor::processBlock(juce::AudioBuffer<float> &buffer,
                                         juce::MidiBuffer &midiMessages) {
  juce::ignoreUnused(midiMessages);
  juce::ScopedNoDenormals noDenormals;

  auto totalNumInputChannels = getTotalNumInputChannels();
  auto totalNumOutputChannels = getTotalNumOutputChannels();

  // Clear any output channels that don't have input
  for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
    buffer.clear(i, 0, buffer.getNumSamples());

{% if cookiecutter.include_faust == "yes" -%}
  faustBridge.process(buffer);
{% else -%}
  // Your audio processing here
{% endif -%}
}

bool {{cookiecutter.plugin_name}}AudioProcessor::hasEditor() const { return true; }

juce::AudioProcessorEditor *{{cookiecutter.plugin_name}}AudioProcessor::createEditor() {
  return new {{cookiecutter.plugin_name}}AudioProcessorEditor(*this);
}

void {{cookiecutter.plugin_name}}AudioProcessor::getStateInformation(juce::MemoryBlock &destData) {
{% if cookiecutter.include_faust == "yes" -%}
  auto state = apvts.copyState();
  std::unique_ptr<juce::XmlElement> xml(state.createXml());
  copyXmlToBinary(*xml, destData);
{% else -%}
  // Save your plugin state here
  juce::ignoreUnused(destData);
{% endif -%}
}

void {{cookiecutter.plugin_name}}AudioProcessor::setStateInformation(const void *data,
                                                int sizeInBytes) {
{% if cookiecutter.include_faust == "yes" -%}
  std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
  if (xml && xml->hasTagName(apvts.state.getType()))
    apvts.replaceState(juce::ValueTree::fromXml(*xml));
{% else -%}
  // Restore your plugin state here
  juce::ignoreUnused(data, sizeInBytes);
{% endif -%}
}

juce::AudioProcessor *JUCE_CALLTYPE createPluginFilter() {
  return new {{cookiecutter.plugin_name}}AudioProcessor();
}
