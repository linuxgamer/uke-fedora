// SPDX-License-Identifier: GPL-2.0-only
// Parse a coherent persist snapshot in memory. Never log or serialize readings
// to a file; DSP transport is a separate, explicitly qualified operation.
#ifndef UKE_SPEAKER_CALIBRATION_HPP
#define UKE_SPEAKER_CALIBRATION_HPP

#include <array>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string_view>

namespace uke::audio {

enum class SpeakerPosition : uint32_t {
    bottom_right = 1, top_right = 2, bottom_left = 4, top_left = 8,
};

struct CalibrationChannel {
    SpeakerPosition position{};
    int32_t resistance_q12 = 0;
};

struct CalibrationSnapshot {
    // Preserve the stock file's CH index. It is not the ALSA/TDM slot index.
    std::array<CalibrationChannel, 4> channel{};
};

inline void require_calibration(bool condition) {
    if (!condition) throw std::runtime_error("invalid or inconsistent speaker calibration");
}

inline void trim_space(std::string_view &text) {
    while (!text.empty() && (text.front() == ' ' || text.front() == '\t')) text.remove_prefix(1);
}

inline void consume(std::string_view &text, std::string_view expected) {
    require_calibration(text.starts_with(expected));
    text.remove_prefix(expected.size());
}

inline int32_t calibration_integer(std::string_view &text) {
    int32_t value = 0;
    auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    require_calibration(result.ec == std::errc{} && result.ptr != text.data());
    text.remove_prefix(size_t(result.ptr - text.data()));
    return value;
}

inline SpeakerPosition calibration_position(std::string_view label) {
    if (label == "TL") return SpeakerPosition::top_left;
    if (label == "TR") return SpeakerPosition::top_right;
    if (label == "BL") return SpeakerPosition::bottom_left;
    if (label == "BR") return SpeakerPosition::bottom_right;
    throw std::runtime_error("unrecognized speaker calibration position");
}

inline CalibrationSnapshot parse_calibration(std::span<const uint8_t> binary,
                                               std::string_view text) {
    require_calibration(binary.size() == 16 && !text.empty() && text.size() <= 2048);
    CalibrationSnapshot snapshot;
    unsigned channels = 0, positions = 0;
    while (!text.empty()) {
        auto end = text.find('\n');
        auto line = text.substr(0, end);
        text = end == text.npos ? std::string_view{} : text.substr(end + 1);
        if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
        trim_space(line);
        require_calibration(!line.empty());
        consume(line, "CH[");
        int32_t index = calibration_integer(line);
        require_calibration(index >= 0 && index < 4 && !(channels & (1u << index)));
        consume(line, "]");
        require_calibration(!line.empty() && (line.front() == ' ' || line.front() == '\t'));
        trim_space(line);
        require_calibration(line.size() >= 3 && (line[2] == ' ' || line[2] == '\t'));
        auto position = calibration_position(line.substr(0, 2));
        line.remove_prefix(2);
        trim_space(line);
        int32_t raw = calibration_integer(line);
        require_calibration(raw > 0);
        trim_space(line);
        consume(line, "(");
        auto close = line.find(')');
        require_calibration(close != line.npos && close > 0 && close < 32);
        auto decimal = line.substr(0, close);
        double ohms = 0;
        auto number = std::from_chars(decimal.data(), decimal.data() + decimal.size(),
                                       ohms, std::chars_format::fixed);
        require_calibration(number.ec == std::errc{} && number.ptr == decimal.data() + decimal.size()
                            && std::isfinite(ohms) && ohms > 0);
        auto dot = decimal.find('.');
        auto precision = dot == decimal.npos ? 0 : decimal.size() - dot - 1;
        require_calibration(precision <= 9);
        double rounding = 0.5 * std::pow(10.0, -double(precision));
        require_calibration(std::abs(ohms - double(raw) / 4096.0) <= rounding + 1e-12);
        line.remove_prefix(close + 1);
        trim_space(line);
        require_calibration(line.empty());
        size_t offset = size_t(index) * 4;
        uint32_t word = uint32_t(binary[offset]) | uint32_t(binary[offset + 1]) << 8 |
                        uint32_t(binary[offset + 2]) << 16 | uint32_t(binary[offset + 3]) << 24;
        require_calibration(word == uint32_t(raw));
        auto bit = uint32_t(position);
        require_calibration(!(positions & bit));
        positions |= bit;
        channels |= 1u << index;
        snapshot.channel[size_t(index)] = {position, raw};
    }
    require_calibration(channels == 15 && positions == 15);
    return snapshot;
}

inline uint8_t amplifier_address(SpeakerPosition position) {
    switch (position) {
    case SpeakerPosition::top_left: return 0x34;
    case SpeakerPosition::top_right: return 0x35;
    case SpeakerPosition::bottom_left: return 0x36;
    case SpeakerPosition::bottom_right: return 0x37;
    }
    throw std::runtime_error("unrecognized speaker position");
}

inline void erase_calibration(CalibrationSnapshot &snapshot) {
    auto *bytes = reinterpret_cast<volatile uint8_t *>(&snapshot);
    for (size_t i = 0; i < sizeof(snapshot); ++i) bytes[i] = 0;
}

} // namespace uke::audio
#endif
