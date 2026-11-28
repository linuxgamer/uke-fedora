// SPDX-License-Identifier: GPL-2.0-only
// Exact generic ACDB parameters, kept opaque. No per-unit data is read here.
// Format reference: AudioReach graphservices 76d04ffb, BSD-3-Clause.
#ifndef UKE_FS19XX_ACDB_HPP
#define UKE_FS19XX_ACDB_HPP
#include <array>
#include <map>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>
#include <openssl/sha.h>
#include "uke-fs19xx-protocol.h"

namespace uke::audio {
using GenericParameters = std::array<std::vector<uint8_t>, 5>;
inline std::string digest(std::span<const uint8_t> data) {
    std::array<unsigned char, SHA256_DIGEST_LENGTH> result{};
    SHA256(data.data(), data.size(), result.data());
    constexpr char hex[] = "0123456789abcdef";
    std::string output;
    for (auto byte : result) { output += hex[byte >> 4]; output += hex[byte & 15]; }
    return output;
}
inline void require_acdb(bool ok) {
    if (!ok) throw std::runtime_error("unsupported or invalid generic speaker DSP data");
}
struct AcdbView {
    std::span<const uint8_t> bytes;
    std::span<const uint8_t> take(size_t n) {
        require_acdb(n <= bytes.size());
        auto result = bytes.first(n); bytes = bytes.subspan(n); return result;
    }
    uint32_t word() { auto p = take(4); return uke_fs19xx_word(p.data()); }
    uint32_t count(size_t stride) {
        auto n = word(); require_acdb(stride && n <= bytes.size() / stride); return n;
    }
    void end() const { require_acdb(bytes.empty()); }
};
inline AcdbView acdb_at(std::span<const uint8_t> bytes, uint32_t offset) {
    require_acdb(offset <= bytes.size()); return {bytes.subspan(offset)};
}
inline GenericParameters parse_foursemi_acdb(std::span<const uint8_t> bytes) {
    require_acdb(bytes.size() == 2838166 &&
        digest(bytes) == "bd3f9b8834b80c23f86241756e263e36ddf92b2b8993ed83ff71c310af952f3e");
    AcdbView file{bytes};
    require_acdb(file.word() == 0x42444341 && file.word() == 0);
    require_acdb(file.word() == file.bytes.size());
    std::map<std::string, std::span<const uint8_t>> chunks;
    while (!file.bytes.empty()) {
        auto tag = file.take(4); auto length = file.word();
        require_acdb(chunks.emplace(std::string(tag.begin(), tag.end()), file.take(length)).second);
    }
    for (const char *name : {"CSLU", "CAKT", "CDLU", "CDDE", "CDDO", "POOL"})
        require_acdb(chunks.contains(name));
    GenericParameters result;
    AcdbView groups{chunks.at("CSLU")};
    auto count = groups.count(8);
    for (uint32_t s = 0; s < count; ++s) {
        auto group = groups.word(), entries = groups.count(8);
        for (uint32_t e = 0; e < entries; ++e) {
            auto key_offset = groups.word(), lut_offset = groups.word();
            if (group != 0xb0000002 && group != 0xb00000d5) continue;
            auto keys = acdb_at(chunks.at("CAKT"), key_offset);
            require_acdb(keys.word() == 0); // exact generic, unselected calibration table
            auto values = acdb_at(chunks.at("CDLU"), lut_offset);
            require_acdb(values.word() == 0);
            auto variants = values.count(12);
            require_acdb(variants == 1);
            auto definitions = acdb_at(chunks.at("CDDE"), values.word());
            auto offsets = acdb_at(chunks.at("CDDO"), values.word());
            values.word(); // persistent DOT2 is never read
            auto parameters = definitions.count(8);
            require_acdb(offsets.count(4) == parameters);
            for (uint32_t p = 0; p < parameters; ++p) {
                auto instance = definitions.word(), parameter = definitions.word();
                auto offset = offsets.word();
                for (size_t slot = 0; slot < result.size(); ++slot) {
                    const auto &expected = uke_fs19xx_parameters[slot];
                    if (instance != expected.instance || parameter != expected.id) continue;
                    require_acdb(result[slot].empty());
                    auto payload = acdb_at(chunks.at("POOL"), offset);
                    require_acdb(payload.word() == expected.bytes);
                    auto data = payload.take(expected.bytes);
                    require_acdb(digest(data) == expected.sha256);
                    result[slot].assign(data.begin(), data.end());
                }
            }
        }
    }
    groups.end();
    for (size_t i = 0; i < result.size(); ++i)
        require_acdb(result[i].size() == uke_fs19xx_parameters[i].bytes);
    return result;
}
} // namespace uke::audio
#endif
