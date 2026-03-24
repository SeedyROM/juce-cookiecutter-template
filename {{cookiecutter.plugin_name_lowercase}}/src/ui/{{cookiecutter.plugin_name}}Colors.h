#pragma once

#include <cmath>

#include <juce_gui_basics/juce_gui_basics.h>

/**
 * {{cookiecutter.plugin_name}} UI colour palette — warm analog aesthetic.
 *
 * Dark charcoal base with warm amber/orange accents,
 * inspired by hardware studio gear.
 */
namespace {{cookiecutter.plugin_name}}Colors {

// ---- Backgrounds ----
inline constexpr juce::uint32 background = 0xff1e1c1a;  // Main background
inline constexpr juce::uint32 panelBg = 0xff2a2725;     // Section panels
inline constexpr juce::uint32 panelBorder = 0xff3a3632; // Panel border / subtle dividers
inline constexpr juce::uint32 topBarBg = 0xff1a1816;    // Top bar (slightly darker)

// ---- Knob ----
inline constexpr juce::uint32 knobBody = 0xff3a3632;      // Knob fill
inline constexpr juce::uint32 knobBodyLight = 0xff4a4642; // Knob gradient top
inline constexpr juce::uint32 knobOutline = 0xff2a2725;   // Knob border
inline constexpr juce::uint32 knobPointer = 0xffe8a96a;   // Knob pointer / notch
inline constexpr juce::uint32 knobTrackBg = 0xff2a2725;   // Arc background
inline constexpr juce::uint32 knobArc = 0xffd4874d;       // Active arc (warm amber)
inline constexpr juce::uint32 knobArcBright = 0xffe8a96a; // Arc highlight end

// ---- Text ----
inline constexpr juce::uint32 labelText = 0xffc8bfb4;    // Label text (warm off-white)
inline constexpr juce::uint32 valueText = 0xffe8a96a;    // Value readout (amber)
inline constexpr juce::uint32 sectionTitle = 0xff8a7e72; // Section header text (muted warm)
inline constexpr juce::uint32 titleText = 0xffd4c5b0;    // Plugin title text

// ---- Toggle / Special ----
inline constexpr juce::uint32 toggleOff = 0xff4a4642;  // Toggle button inactive
inline constexpr juce::uint32 toggleOn = 0xff7ab8d4;   // Toggle button active (ice blue)
inline constexpr juce::uint32 toggleGlow = 0x407ab8d4; // Toggle glow (transparent ice blue)

// ---- Accent ----
inline constexpr juce::uint32 accentWarm = 0xffd4874d;   // Primary warm accent
inline constexpr juce::uint32 accentBright = 0xffe8a96a; // Bright warm accent

// ---- Metering ----
inline constexpr juce::uint32 meterGreen = 0xff7dc96b;
inline constexpr juce::uint32 meterYellow = 0xffe6cf63;
inline constexpr juce::uint32 meterOrange = 0xffe39a57;
inline constexpr juce::uint32 meterRed = 0xffd85c4b;

inline float peakToMeterDb(float peak) {
  return 20.0f * std::log10(juce::jmax(peak, 1.0e-6f));
}

inline float peakToMeterNormalised(float peak) {
  return juce::jlimit(0.0f, 1.0f, (peakToMeterDb(peak) + 60.0f) / 60.0f);
}

inline juce::Colour meterColourForPeak(float peak) {
  const auto db = peakToMeterDb(peak);
  if (db >= -3.0f)
    return juce::Colour(meterRed);
  if (db >= -9.0f)
    return juce::Colour(meterOrange);
  if (db >= -18.0f)
    return juce::Colour(meterYellow);
  return juce::Colour(meterGreen);
}

} // namespace {{cookiecutter.plugin_name}}Colors
