#include "PluginPresetManager.h"

namespace {

constexpr auto presetFileExtension = ".{{cookiecutter.plugin_name_lowercase}}preset";
constexpr auto presetRootType = "PluginStateRoot";

juce::CriticalSection presetCacheLock;
juce::Identifier cachedPluginStateType;
juce::ValueTree cachedReferenceState;
std::vector<PluginPresetManager::PresetInfo> cachedFactoryPresets;
std::vector<PluginPresetManager::PresetInfo> cachedAvailablePresets;
bool hasCachedFactoryPresets = false;
bool hasCachedAvailablePresets = false;
bool userPresetListDirty = true;

juce::ValueTree createPresetState(const juce::ValueTree& referenceState,
                                  std::initializer_list<std::pair<const char*, float>> values) {
  auto state = referenceState.createCopy();

  auto setParam = [&state](const juce::String& paramID, float value) {
    for (int i = 0; i < state.getNumChildren(); ++i) {
      auto child = state.getChild(i);
      if (child.hasProperty("id") && child["id"].toString() == paramID) {
        child.setProperty("value", value, nullptr);
        return;
      }
    }
  };

  for (const auto& [paramID, value] : values)
    setParam(paramID, value);

  return state;
}

std::vector<PluginPresetManager::PresetInfo>
createFactoryPresets(const juce::ValueTree& referenceState, const juce::Identifier& pluginStateType) {
  juce::ignoreUnused(pluginStateType);

  // No factory presets by default. Add your own here, e.g.:
  {% raw %}// {"MyPreset", true, {}, createPresetState(referenceState, {{"param", 0.5f}})},{% endraw %}
  juce::ignoreUnused(referenceState);
  return {};
}

PluginPresetManager::PresetInfo* findPresetByName(std::vector<PluginPresetManager::PresetInfo>& presets,
                                                   const juce::String& presetName) {
  for (auto& preset : presets)
    if (preset.name == presetName)
      return &preset;

  return nullptr;
}

juce::ValueTree loadWrappedStateFromFile(const juce::File& file) {
  if (!file.existsAsFile())
    return {};

  auto xml = juce::XmlDocument::parse(file);
  return xml != nullptr ? juce::ValueTree::fromXml(*xml) : juce::ValueTree{};
}

juce::File getPresetDirectoryForCache() {
  auto directory = juce::File::getSpecialLocation(juce::File::userApplicationDataDirectory)
                       .getChildFile("{{cookiecutter.company_name}}")
                       .getChildFile("{{cookiecutter.plugin_name}}")
                       .getChildFile("Presets");
  directory.createDirectory();
  return directory;
}

bool shouldRebuildFactoryPresets(const juce::ValueTree& referenceState,
                                 const juce::Identifier& pluginStateType) {
  if (!hasCachedFactoryPresets)
    return true;

  if (cachedPluginStateType != pluginStateType)
    return true;

  return !cachedReferenceState.isEquivalentTo(referenceState);
}

void rebuildFactoryPresetCache(const juce::ValueTree& referenceState,
                               const juce::Identifier& pluginStateType) {
  cachedFactoryPresets = createFactoryPresets(referenceState, pluginStateType);
  cachedReferenceState = referenceState.createCopy();
  cachedPluginStateType = pluginStateType;
  hasCachedFactoryPresets = true;
  userPresetListDirty = true;
}

void rebuildAvailablePresetCache() {
  cachedAvailablePresets = cachedFactoryPresets;

  auto directory = getPresetDirectoryForCache();
  auto files =
      directory.findChildFiles(juce::File::findFiles, false, "*" + juce::String(presetFileExtension));

  for (const auto& file : files)
    cachedAvailablePresets.push_back({file.getFileNameWithoutExtension(), false, file, {}});

  std::sort(cachedAvailablePresets.begin(),
            cachedAvailablePresets.end(),
            [](const PluginPresetManager::PresetInfo& lhs, const PluginPresetManager::PresetInfo& rhs) {
              if (lhs.isFactory != rhs.isFactory)
                return lhs.isFactory;
              return lhs.name < rhs.name;
            });

  hasCachedAvailablePresets = true;
  userPresetListDirty = false;
}

void ensurePresetCaches(const juce::ValueTree& referenceState, const juce::Identifier& pluginStateType) {
  if (shouldRebuildFactoryPresets(referenceState, pluginStateType))
    rebuildFactoryPresetCache(referenceState, pluginStateType);

  if (!hasCachedAvailablePresets || userPresetListDirty)
    rebuildAvailablePresetCache();
}

} // namespace

juce::File PluginPresetManager::getPresetDirectory() {
  auto directory = juce::File::getSpecialLocation(juce::File::userApplicationDataDirectory)
                       .getChildFile("{{cookiecutter.company_name}}")
                       .getChildFile("{{cookiecutter.plugin_name}}")
                       .getChildFile("Presets");
  directory.createDirectory();
  return directory;
}

std::vector<PluginPresetManager::PresetInfo>
PluginPresetManager::getAvailablePresets(const juce::ValueTree& referenceState,
                                         const juce::Identifier& pluginStateType) {
  const juce::ScopedLock lock(presetCacheLock);
  ensurePresetCaches(referenceState, pluginStateType);
  return cachedAvailablePresets;
}

juce::ValueTree PluginPresetManager::loadPresetState(const juce::String& presetName,
                                                     const juce::ValueTree& referenceState,
                                                     const juce::Identifier& pluginStateType) {
  std::vector<PluginPresetManager::PresetInfo> presets;
  {
    const juce::ScopedLock lock(presetCacheLock);
    ensurePresetCaches(referenceState, pluginStateType);
    presets = cachedAvailablePresets;
  }

  auto* preset = findPresetByName(presets, presetName);
  if (preset == nullptr)
    return {};

  if (preset->isFactory)
    return preset->state.createCopy();

  auto wrappedState = loadWrappedStateFromFile(preset->file);
  if (!wrappedState.hasType(presetRootType))
    return {};

  auto pluginState = wrappedState.getChildWithName(pluginStateType);
  return pluginState.isValid() ? pluginState.createCopy() : juce::ValueTree{};
}

bool PluginPresetManager::saveUserPreset(const juce::String& presetName,
                                         const juce::ValueTree& wrappedState) {
  if (presetName.trim().isEmpty() || !wrappedState.isValid())
    return false;

  auto file = getPresetDirectory().getChildFile(presetName + presetFileExtension);
  std::unique_ptr<juce::XmlElement> xml(wrappedState.createXml());
  const auto didSave = xml != nullptr && xml->writeTo(file);
  if (didSave) {
    const juce::ScopedLock lock(presetCacheLock);
    userPresetListDirty = true;
  }

  return didSave;
}

bool PluginPresetManager::deleteUserPreset(const juce::String& presetName) {
  auto file = getPresetDirectory().getChildFile(presetName + presetFileExtension);
  const auto didDelete = file.existsAsFile() && file.deleteFile();
  if (didDelete) {
    const juce::ScopedLock lock(presetCacheLock);
    userPresetListDirty = true;
  }

  return didDelete;
}

void PluginPresetManager::revealPresetDirectory() {
  getPresetDirectory().revealToUser();
}

bool PluginPresetManager::isFactoryPreset(const juce::String& presetName,
                                          const juce::ValueTree& referenceState,
                                          const juce::Identifier& pluginStateType) {
  std::vector<PluginPresetManager::PresetInfo> presets;
  {
    const juce::ScopedLock lock(presetCacheLock);
    ensurePresetCaches(referenceState, pluginStateType);
    presets = cachedAvailablePresets;
  }

  auto* preset = findPresetByName(presets, presetName);
  return preset != nullptr && preset->isFactory;
}
