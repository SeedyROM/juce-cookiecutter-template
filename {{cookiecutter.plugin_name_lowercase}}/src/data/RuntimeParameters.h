#pragma once

{% if cookiecutter.include_faust == "yes" -%}
#include "FaustParams.h"

namespace RuntimeParamIDs = FaustParamIDs;

namespace RuntimeParameters {
inline juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
  return FaustParams::createLayout();
}
} // namespace RuntimeParameters
{% else -%}
#include "data/PluginParameters.h"

namespace RuntimeParamIDs = PluginParamIDs;

namespace RuntimeParameters {
inline juce::AudioProcessorValueTreeState::ParameterLayout createLayout() {
  return PluginParameters::createLayout();
}
} // namespace RuntimeParameters
{% endif %}
