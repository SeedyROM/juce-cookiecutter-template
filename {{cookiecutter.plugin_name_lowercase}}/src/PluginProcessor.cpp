#include "PluginProcessor.h"
#include "PluginEditor.h"

#include <cmath>

namespace {

constexpr auto pluginStateRootType = "PluginStateRoot";
constexpr auto pluginStatePropertySchemaVersion = "schemaVersion";
constexpr auto pluginStatePropertyPluginVersion = "pluginVersion";
constexpr auto pluginStatePropertyActiveABSlot = "activeABSlot";
constexpr auto pluginStatePropertySlotAPresetName = "slotAPresetName";
constexpr auto pluginStatePropertySlotBPresetName = "slotBPresetName";
constexpr auto pluginStateChildSlotA = "slotAState";
constexpr auto pluginStateChildSlotB = "slotBState";
constexpr auto abSlotNameA = "A";
constexpr auto abSlotNameB = "B";

} // namespace

{{cookiecutter.plugin_name}}AudioProcessor::{{cookiecutter.plugin_name}}AudioProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      apvts(*this, nullptr, "Parameters", RuntimeParameters::createLayout())
{% if cookiecutter.include_faust == "yes" -%}
      ,
      faustBridge(apvts)
{% endif -%}
{
  defaultPresetState = captureCurrentState();
  initialiseABSlotsFromCurrentState();
}

{{cookiecutter.plugin_name}}AudioProcessor::~{{cookiecutter.plugin_name}}AudioProcessor() {}

const juce::String {{cookiecutter.plugin_name}}AudioProcessor::getName() const {
  return JucePlugin_Name;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::acceptsMidi() const {
  return false;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::producesMidi() const {
  return false;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::isMidiEffect() const {
  return false;
}

double {{cookiecutter.plugin_name}}AudioProcessor::getTailLengthSeconds() const {
  return 0.0;
}

int {{cookiecutter.plugin_name}}AudioProcessor::getNumPrograms() {
  return 1;
}

int {{cookiecutter.plugin_name}}AudioProcessor::getCurrentProgram() {
  return 0;
}

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
  currentSampleRate = sampleRate;
  inputMeterPeak.store(0.0f);
  outputMeterPeak.store(0.0f);
  meterSamplesSinceLastUpdate = 0;
  meterUpdateIntervalSamples = juce::jmax(256, samplesPerBlock);

{% if cookiecutter.include_faust == "yes" -%}
  faustBridge.prepare(sampleRate, samplesPerBlock);
{% endif -%}
}

void {{cookiecutter.plugin_name}}AudioProcessor::releaseResources() {
  // Release resources here
}

juce::ValueTree {{cookiecutter.plugin_name}}AudioProcessor::captureCurrentState() {
  auto state = apvts.copyState();
  sanitiseTransientState(state);
  return state;
}

juce::ValueTree {{cookiecutter.plugin_name}}AudioProcessor::createWrappedPluginState(bool includeABState) {
  juce::ValueTree wrappedState(pluginStateRootType);
  wrappedState.setProperty(pluginStatePropertySchemaVersion, stateSchemaVersion, nullptr);
  wrappedState.setProperty(pluginStatePropertyPluginVersion, JucePlugin_VersionString, nullptr);
  syncActiveABSlotFromCurrentState();
  wrappedState.appendChild(captureCurrentState(), nullptr);

  if (includeABState) {
    wrappedState.setProperty(pluginStatePropertyActiveABSlot,
                             activeABSlot == ABSlot::A ? abSlotNameA : abSlotNameB,
                             nullptr);
    wrappedState.setProperty(pluginStatePropertySlotAPresetName, slotAPresetName, nullptr);
    wrappedState.setProperty(pluginStatePropertySlotBPresetName, slotBPresetName, nullptr);

    juce::ValueTree slotAWrapper(pluginStateChildSlotA);
    slotAWrapper.appendChild(slotAState.createCopy(), nullptr);
    wrappedState.appendChild(slotAWrapper, nullptr);

    juce::ValueTree slotBWrapper(pluginStateChildSlotB);
    slotBWrapper.appendChild(slotBState.createCopy(), nullptr);
    wrappedState.appendChild(slotBWrapper, nullptr);
  }

  return wrappedState;
}

juce::ValueTree {{cookiecutter.plugin_name}}AudioProcessor::migrateStateTree(juce::ValueTree savedTree) const {
  auto schemaVersion = savedTree.getProperty(pluginStatePropertySchemaVersion);
  if (!schemaVersion.isInt() || static_cast<int>(schemaVersion) < 1)
    savedTree.setProperty(pluginStatePropertySchemaVersion, stateSchemaVersion, nullptr);

  if (!savedTree.hasProperty(pluginStatePropertyPluginVersion))
    savedTree.setProperty(pluginStatePropertyPluginVersion, JucePlugin_VersionString, nullptr);

  if (!savedTree.hasProperty(pluginStatePropertyActiveABSlot))
    savedTree.setProperty(pluginStatePropertyActiveABSlot, abSlotNameA, nullptr);

  if (!savedTree.hasProperty(pluginStatePropertySlotAPresetName))
    savedTree.setProperty(pluginStatePropertySlotAPresetName, "Init", nullptr);

  if (!savedTree.hasProperty(pluginStatePropertySlotBPresetName))
    savedTree.setProperty(pluginStatePropertySlotBPresetName, "Init", nullptr);

  return savedTree;
}

juce::ValueTree
{{cookiecutter.plugin_name}}AudioProcessor::extractPluginStateFromSavedTree(const juce::ValueTree &savedTree) const {
  if (!savedTree.isValid())
    return {};

  if (savedTree.hasType(apvts.state.getType()))
    return savedTree.createCopy();

  if (!savedTree.hasType(pluginStateRootType))
    return {};

  auto migratedTree = migrateStateTree(savedTree.createCopy());
  auto pluginState = migratedTree.getChildWithName(apvts.state.getType());
  return pluginState.isValid() ? pluginState.createCopy() : juce::ValueTree{};
}

void {{cookiecutter.plugin_name}}AudioProcessor::applyStateToApvts(const juce::ValueTree &stateToApply) {
  if (!stateToApply.isValid())
    return;

  const juce::ScopedValueSetter<bool> applyingState(isApplyingABState, true);
  apvts.replaceState(stateToApply.createCopy());
}

void {{cookiecutter.plugin_name}}AudioProcessor::initialiseABSlotsFromCurrentState() {
  auto currentState = captureCurrentState();
  slotAState = currentState.createCopy();
  slotBState = currentState.createCopy();
  activeABSlot = ABSlot::A;
  slotAPresetName = "Init";
  slotBPresetName = "Init";
}

void {{cookiecutter.plugin_name}}AudioProcessor::syncActiveABSlotFromCurrentState() {
  if (isApplyingABState)
    return;

  getMutableABState(activeABSlot) = captureCurrentState();
}

void {{cookiecutter.plugin_name}}AudioProcessor::sanitiseTransientState(juce::ValueTree &state) const {
  juce::ignoreUnused(state);
}

void {{cookiecutter.plugin_name}}AudioProcessor::setActivePresetName(const juce::String &presetName) {
  if (activeABSlot == ABSlot::A)
    slotAPresetName = presetName;
  else
    slotBPresetName = presetName;
}

juce::ValueTree &{{cookiecutter.plugin_name}}AudioProcessor::getMutableABState(ABSlot slot) {
  return slot == ABSlot::A ? slotAState : slotBState;
}

const juce::ValueTree &{{cookiecutter.plugin_name}}AudioProcessor::getABState(ABSlot slot) const {
  return slot == ABSlot::A ? slotAState : slotBState;
}

void {{cookiecutter.plugin_name}}AudioProcessor::setActiveABSlot(ABSlot slot) {
  if (slot == activeABSlot)
    return;

  syncActiveABSlotFromCurrentState();
  activeABSlot = slot;
  applyStateToApvts(getABState(activeABSlot));
}

void {{cookiecutter.plugin_name}}AudioProcessor::copyABSlot(ABSlot from, ABSlot to) {
  syncActiveABSlotFromCurrentState();
  getMutableABState(to) = getABState(from).createCopy();
  if (from == ABSlot::A)
    slotBPresetName = slotAPresetName;
  else
    slotAPresetName = slotBPresetName;

  if (activeABSlot == to)
    applyStateToApvts(getABState(to));
}

void {{cookiecutter.plugin_name}}AudioProcessor::swapABSlots() {
  syncActiveABSlotFromCurrentState();
  auto previousA = slotAState.createCopy();
  auto previousName = slotAPresetName;
  slotAState = slotBState.createCopy();
  slotBState = previousA;
  slotAPresetName = slotBPresetName;
  slotBPresetName = previousName;
  applyStateToApvts(getABState(activeABSlot));
}

juce::StringArray {{cookiecutter.plugin_name}}AudioProcessor::getAvailablePresetNames() const {
  juce::StringArray names;
  for (const auto &preset :
       PluginPresetManager::getAvailablePresets(defaultPresetState, apvts.state.getType()))
    names.add(preset.name);
  return names;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::hasDistinctABState() const {
  return !slotAState.isEquivalentTo(slotBState);
}

juce::String {{cookiecutter.plugin_name}}AudioProcessor::getActivePresetName() const {
  return activeABSlot == ABSlot::A ? slotAPresetName : slotBPresetName;
}

juce::String {{cookiecutter.plugin_name}}AudioProcessor::getDisplayedPresetName() {
  syncActiveABSlotFromCurrentState();

  const auto activePresetName = getActivePresetName();
  const auto currentState = captureCurrentState();
  const auto presetState =
      PluginPresetManager::loadPresetState(activePresetName, defaultPresetState, apvts.state.getType());

  if (!presetState.isValid())
    return activePresetName;

  return currentState.isEquivalentTo(presetState) ? activePresetName : "Custom";
}

bool {{cookiecutter.plugin_name}}AudioProcessor::isActivePresetFactory() const {
  return PluginPresetManager::isFactoryPreset(
      getActivePresetName(), defaultPresetState, apvts.state.getType());
}

bool {{cookiecutter.plugin_name}}AudioProcessor::loadPreset(const juce::String &presetName) {
  auto presetState =
      PluginPresetManager::loadPresetState(presetName, defaultPresetState, apvts.state.getType());
  if (!presetState.isValid())
    return false;

  getMutableABState(activeABSlot) = presetState.createCopy();
  setActivePresetName(presetName);
  applyStateToApvts(getABState(activeABSlot));
  return true;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::saveUserPreset(const juce::String &presetName) {
  syncActiveABSlotFromCurrentState();
  auto wrappedState = createWrappedPluginState(false);
  if (!PluginPresetManager::saveUserPreset(presetName, wrappedState))
    return false;

  setActivePresetName(presetName);
  return true;
}

bool {{cookiecutter.plugin_name}}AudioProcessor::deleteActiveUserPreset() {
  auto presetName = getActivePresetName();
  if (presetName.isEmpty() ||
      PluginPresetManager::isFactoryPreset(presetName, defaultPresetState, apvts.state.getType()))
    return false;

  if (!PluginPresetManager::deleteUserPreset(presetName))
    return false;

  setActivePresetName("Init");
  return true;
}

void {{cookiecutter.plugin_name}}AudioProcessor::revealPresetDirectory() const {
  PluginPresetManager::revealPresetDirectory();
}

void {{cookiecutter.plugin_name}}AudioProcessor::clearABState() {
  syncActiveABSlotFromCurrentState();
  slotBState = slotAState.createCopy();
  slotBPresetName = slotAPresetName;
  activeABSlot = ABSlot::A;
}

void {{cookiecutter.plugin_name}}AudioProcessor::updatePeakMeter(std::atomic<float> &meterState,
                                              float blockPeak,
                                              int numSamples) noexcept {
  const auto heldPeak = meterState.load(std::memory_order_relaxed);
  if (blockPeak >= heldPeak) {
    meterState.store(blockPeak, std::memory_order_relaxed);
    return;
  }

  const auto decayTimeSeconds = 0.16f;
  const auto decay =
      std::exp(-static_cast<float>(numSamples) /
               static_cast<float>(juce::jmax(1.0, currentSampleRate * decayTimeSeconds)));
  meterState.store(heldPeak * decay, std::memory_order_relaxed);
}

bool {{cookiecutter.plugin_name}}AudioProcessor::isBusesLayoutSupported(const BusesLayout &layouts) const {
  const auto mainInput = layouts.getMainInputChannelSet();
  const auto mainOutput = layouts.getMainOutputChannelSet();

  if (mainOutput != juce::AudioChannelSet::stereo())
    return false;

  if (mainInput != juce::AudioChannelSet::mono() && mainInput != juce::AudioChannelSet::stereo())
    return false;

  return true;
}

void {{cookiecutter.plugin_name}}AudioProcessor::processBlock(juce::AudioBuffer<float> &buffer,
                                          juce::MidiBuffer &midiMessages) {
  juce::ignoreUnused(midiMessages);
  juce::ScopedNoDenormals noDenormals;

  const auto totalNumInputChannels = getTotalNumInputChannels();
  const auto totalNumOutputChannels = getTotalNumOutputChannels();

  for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
    buffer.clear(i, 0, buffer.getNumSamples());

  auto getMaxPeak = [&buffer](int numChannels) {
    auto peak = 0.0f;
    for (int ch = 0; ch < numChannels; ++ch)
      peak = juce::jmax(peak, buffer.getMagnitude(ch, 0, buffer.getNumSamples()));
    return peak;
  };

  meterSamplesSinceLastUpdate += buffer.getNumSamples();
  const bool shouldMeasurePeaks = meterSamplesSinceLastUpdate >= meterUpdateIntervalSamples;
  if (shouldMeasurePeaks) {
    updatePeakMeter(inputMeterPeak,
                    juce::jlimit(0.0f, 1.2f, getMaxPeak(totalNumInputChannels)),
                    meterSamplesSinceLastUpdate);
  }

{% if cookiecutter.include_faust == "yes" -%}
  faustBridge.process(buffer, totalNumInputChannels, totalNumOutputChannels);
{% else -%}
  // TODO: Add your DSP processing here.
  // Access parameters via apvts.getRawParameterValue("paramId")->load()
  juce::ignoreUnused(buffer);
{% endif -%}

  if (shouldMeasurePeaks) {
    updatePeakMeter(outputMeterPeak,
                    juce::jlimit(0.0f, 1.2f, getMaxPeak(totalNumOutputChannels)),
                    meterSamplesSinceLastUpdate);
    meterSamplesSinceLastUpdate = 0;
  }
}

bool {{cookiecutter.plugin_name}}AudioProcessor::hasEditor() const {
  return true;
}

juce::AudioProcessorEditor *{{cookiecutter.plugin_name}}AudioProcessor::createEditor() {
  return new {{cookiecutter.plugin_name}}AudioProcessorEditor(*this);
}

void {{cookiecutter.plugin_name}}AudioProcessor::getStateInformation(juce::MemoryBlock &destData) {
  auto state = createWrappedPluginState(true);
  std::unique_ptr<juce::XmlElement> xml(state.createXml());
  copyXmlToBinary(*xml, destData);
}

void {{cookiecutter.plugin_name}}AudioProcessor::setStateInformation(const void *data,
                                                 int sizeInBytes) {
  std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
  if (xml == nullptr)
    return;

  auto restoredTree = juce::ValueTree::fromXml(*xml);
  auto pluginState = extractPluginStateFromSavedTree(restoredTree);
  if (!pluginState.isValid())
    return;

  applyStateToApvts(pluginState);

  if (restoredTree.hasType(pluginStateRootType)) {
    auto migratedTree = migrateStateTree(restoredTree.createCopy());
    auto restoredSlotAWrapper = migratedTree.getChildWithName(pluginStateChildSlotA);
    auto restoredSlotBWrapper = migratedTree.getChildWithName(pluginStateChildSlotB);

    auto restoredSlotA = restoredSlotAWrapper.getChildWithName(apvts.state.getType());
    auto restoredSlotB = restoredSlotBWrapper.getChildWithName(apvts.state.getType());

    if (restoredSlotA.isValid() && restoredSlotB.isValid()) {
      slotAState = restoredSlotA.createCopy();
      slotBState = restoredSlotB.createCopy();
      slotAPresetName = migratedTree[pluginStatePropertySlotAPresetName].toString();
      slotBPresetName = migratedTree[pluginStatePropertySlotBPresetName].toString();
      activeABSlot = migratedTree[pluginStatePropertyActiveABSlot].toString() == abSlotNameB
                         ? ABSlot::B
                         : ABSlot::A;
      applyStateToApvts(getABState(activeABSlot));
      return;
    }
  }

  initialiseABSlotsFromCurrentState();
}

juce::AudioProcessor *JUCE_CALLTYPE createPluginFilter() {
  return new {{cookiecutter.plugin_name}}AudioProcessor();
}
