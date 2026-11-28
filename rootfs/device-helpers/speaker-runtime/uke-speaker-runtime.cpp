// SPDX-License-Identifier: GPL-2.0-only
// Unit calibration flows from read-only persist to the kernel/DSP in memory.
#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <string_view>
#include <iostream>
#include <memory>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/resource.h>
#include <alsa/asoundlib.h>
#include <openssl/crypto.h>
#include "uke-fs19xx-acdb.hpp"
#include "uke-speaker-persist.hpp"

namespace {
using namespace uke::audio;
struct PrivateSession {
    CalibrationSnapshot calibration;
    std::array<uint8_t, UKE_FS19XX_FRAME_BYTES> frame{};
    ~PrivateSession() {
        erase_calibration(calibration);
        volatile uint8_t *p = frame.data();
        for (size_t i = 0; i < frame.size(); ++i) p[i] = 0;
    }
};
void require_runtime(bool ok) {
    if (!ok) throw std::runtime_error("speaker runtime operation rejected");
}
GenericParameters generic_parameters(const char *path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    require_acdb(file && file.tellg() == 2838166);
    std::vector<uint8_t> data(2838166);
    file.seekg(0);
    require_acdb(bool(file.read(reinterpret_cast<char *>(data.data()), data.size())));
    return parse_foursemi_acdb(data);
}
struct Control {
    snd_ctl_t *handle = nullptr;
    snd_ctl_elem_id_t *id = nullptr;
    bool locked = false;
    explicit Control(const char *card, bool read_only = false) {
        require_runtime(snd_ctl_elem_id_malloc(&id) == 0);
        if (snd_ctl_open(&handle, card, read_only ? SND_CTL_READONLY : 0) < 0) {
            snd_ctl_elem_id_free(id); id = nullptr;
            throw std::runtime_error("protected speaker control unavailable");
        }
        snd_ctl_elem_id_set_interface(id, SND_CTL_ELEM_IFACE_MIXER);
        snd_ctl_elem_id_set_name(id, UKE_FS19XX_CONTROL);
    }
    Control(const Control &) = delete;
    ~Control() {
        if (locked) snd_ctl_elem_unlock(handle, id);
        if (handle) snd_ctl_close(handle);
        if (id) snd_ctl_elem_id_free(id);
    }
    static bool trusted_command(const snd_ctl_elem_info_t *info) {
        return snd_ctl_elem_info_get_type(info) == SND_CTL_ELEM_TYPE_BYTES &&
            snd_ctl_elem_info_get_count(info) == UKE_FS19XX_FRAME_BYTES &&
            snd_ctl_elem_info_get_numid(info) != 0 && !snd_ctl_elem_info_is_user(info) &&
            !snd_ctl_elem_info_is_readable(info) && snd_ctl_elem_info_is_writable(info) &&
            snd_ctl_elem_info_is_volatile(info);
    }
    bool trusted_status() const {
        snd_ctl_elem_info_t *info = nullptr;
        if (snd_ctl_elem_info_malloc(&info) < 0) return false;
        snd_ctl_elem_info_set_interface(info, SND_CTL_ELEM_IFACE_MIXER);
        snd_ctl_elem_info_set_name(info, UKE_FS19XX_STATUS);
        const auto result = snd_ctl_elem_info(handle, info);
        const bool valid = result >= 0 &&
            snd_ctl_elem_info_get_type(info) == SND_CTL_ELEM_TYPE_ENUMERATED &&
            snd_ctl_elem_info_get_count(info) == 1 && snd_ctl_elem_info_get_items(info) == 6 &&
            snd_ctl_elem_info_get_numid(info) != 0 && !snd_ctl_elem_info_is_user(info) &&
            snd_ctl_elem_info_is_readable(info) && !snd_ctl_elem_info_is_writable(info) &&
            snd_ctl_elem_info_is_volatile(info);
        snd_ctl_elem_info_free(info);
        return valid;
    }
    bool available() const {
        snd_ctl_elem_info_t *info = nullptr;
        if (snd_ctl_elem_info_malloc(&info) < 0) return false;
        snd_ctl_elem_info_set_id(info, id);
        const auto status = snd_ctl_elem_info(handle, info);
        const bool found = status >= 0 && trusted_command(info);
        snd_ctl_elem_info_free(info);
        return found && trusted_status();
    }
    int status() const {
        require_runtime(trusted_status());
        snd_ctl_elem_id_t *state_id = nullptr;
        snd_ctl_elem_value_t *value = nullptr;
        require_runtime(snd_ctl_elem_id_malloc(&state_id) == 0);
        if (snd_ctl_elem_value_malloc(&value) < 0) {
            snd_ctl_elem_id_free(state_id);
            throw std::runtime_error("speaker status memory unavailable");
        }
        snd_ctl_elem_id_set_interface(state_id, SND_CTL_ELEM_IFACE_MIXER);
        snd_ctl_elem_id_set_name(state_id, UKE_FS19XX_STATUS);
        snd_ctl_elem_value_set_id(value, state_id);
        const int result = snd_ctl_elem_read(handle, value);
        const unsigned state = result >= 0 ? snd_ctl_elem_value_get_enumerated(value, 0) : 6;
        snd_ctl_elem_value_free(value);
        snd_ctl_elem_id_free(state_id);
        require_runtime(result >= 0 && state <= UKE_FS_FAULT);
        return int(state);
    }
    void lock() {
        require_runtime(available());
        snd_ctl_elem_info_t *info = nullptr;
        require_runtime(snd_ctl_elem_info_malloc(&info) == 0);
        snd_ctl_elem_info_set_id(info, id);
        int result = snd_ctl_elem_info(handle, info);
        bool valid = result >= 0 && trusted_command(info);
        if (valid) snd_ctl_elem_info_get_id(info, id);
        snd_ctl_elem_info_free(info);
        require_runtime(valid && snd_ctl_elem_lock(handle, id) >= 0);
        locked = true;
        require_runtime(available());
    }
    void write(std::span<const uint8_t> frame) {
        require_runtime(locked && frame.size() == UKE_FS19XX_FRAME_BYTES && available());
        snd_ctl_elem_value_t *value = nullptr;
        require_runtime(snd_ctl_elem_value_malloc(&value) == 0);
        snd_ctl_elem_value_set_id(value, id);
        for (size_t i = 0; i < frame.size(); ++i)
            snd_ctl_elem_value_set_byte(value, i, frame[i]);
        int result = snd_ctl_elem_write(handle, value);
        // ALSA's temporary userspace value also contains per-unit data.
        snd_ctl_elem_value_clear(value);
        snd_ctl_elem_value_free(value);
        require_runtime(result >= 0);
    }
};
void send(Control &control, PrivateSession &session, uint32_t operation,
          uint32_t transaction, uint32_t slot = 0, uint32_t total = 0,
          uint32_t offset = 0, std::span<const uint8_t> payload = {}) {
    require_runtime(payload.size() <= UKE_FS19XX_DATA_BYTES);
    auto &frame = session.frame;
    std::fill(frame.begin(), frame.end(), 0);
    uint32_t words[] = {UKE_FS19XX_ABI, operation, transaction, slot,
                        total, offset, uint32_t(payload.size()), 0};
    for (size_t i = 0; i < std::size(words); ++i)
        uke_fs19xx_put_word(frame.data() + 4 * i, words[i]);
    std::copy(payload.begin(), payload.end(), frame.begin() + 32);
    control.write(frame);
}
void load(Control &control, PrivateSession &session, const GenericParameters &parameters) {
    uint32_t transaction = 0;
    require_runtime(getrandom(&transaction, sizeof(transaction), 0) == ssize_t(sizeof(transaction)) && transaction);
    try {
        send(control, session, UKE_FS_BEGIN, transaction);
        for (size_t slot = 0; slot < parameters.size(); ++slot) {
            const auto &data = parameters[slot];
            for (size_t offset = 0; offset < data.size(); offset += UKE_FS19XX_DATA_BYTES)
                send(control, session, UKE_FS_PARAMETER, transaction, slot, data.size(), offset,
                    std::span(data).subspan(offset, std::min<size_t>(UKE_FS19XX_DATA_BYTES, data.size() - offset)));
        }
        // No file is created. CH ordinal is retained; labels are carried separately.
        std::fill(session.frame.begin(), session.frame.end(), 0);
        std::array<uint8_t, 112> payload{};
        for (size_t i = 0; i < session.calibration.channel.size(); ++i) {
            const auto &channel = session.calibration.channel[i];
            uke_fs19xx_put_word(payload.data() + 4 * i, uint32_t(channel.position));
            uke_fs19xx_put_word(payload.data() + 16 + 24 * i, uint32_t(channel.resistance_q12));
        }
        // mlockall protects this temporary too; erase it before propagating errors.
        try { send(control, session, UKE_FS_CALIBRATION, transaction, 0, 112, 0, payload); }
        catch (...) { OPENSSL_cleanse(payload.data(), payload.size()); throw; }
        OPENSSL_cleanse(payload.data(), payload.size());
        send(control, session, UKE_FS_COMMIT, transaction);
    } catch (...) {
        try { send(control, session, UKE_FS_CLEAR, transaction); } catch (...) {}
        throw;
    }
}
} // namespace

int main(int argc, char **argv) {
    const char *directory = "/mnt/vendor/persist/audio";
    const char *acdb = "/var/cache/uke-speaker-runtime/Forte_acdb_cal.acdb";
    const char *card = "hw:POCOPadX1";
    bool apply = false, status_only = false, has_control = false, gain_readiness = false;
    bool ensure_loaded = false;
    unsigned operations = 0;
    try {
        for (int i = 1; i < argc; ++i) {
            std::string_view option(argv[i]);
            if (option == "--check") { apply = false; ++operations; }
            else if (option == "--load") { apply = true; ++operations; }
            else if (option == "--ensure-loaded") { apply = true; ensure_loaded = true; ++operations; }
            else if (option == "--status") { status_only = true; ++operations; }
            else if (option == "--has-control") { has_control = true; ++operations; }
            else if (option == "--gain-readiness") { gain_readiness = true; ++operations; }
            else if (option == "--persist-directory" && i + 1 < argc) directory = argv[++i];
            else if (option == "--acdb" && i + 1 < argc) acdb = argv[++i];
            else if (option == "--card" && i + 1 < argc) card = argv[++i];
            else throw std::runtime_error("usage: uke-speaker-runtime [--check|--load|--ensure-loaded|--status|--has-control|--gain-readiness] [--acdb PATH] [--persist-directory RO_PATH] [--card ALSA_ID]");
        }
        require_runtime(operations <= 1);
        if (gain_readiness) {
            bool authenticated = false;
            int state = -1;
            try {
                Control control(card, true);
                authenticated = control.available();
                if (authenticated) state = control.status();
            } catch (const std::exception &) {
                // Metadata errors remain blocked. No tuning or private source
                // is opened, no stream is started and no ALSA write is issued.
            }
            static constexpr const char *names[] = {"empty", "staging", "ready", "prepared", "running", "fault"};
            std::cout << "{\"schema_version\":1,\"requested_gain_ceiling\":243,"
                << "\"binary_gain_ceiling\":223,\"gain_243_admissible\":false,\"decision\":\"blocked\","
                << "\"authenticated_interface\":" << (authenticated ? "true" : "false")
                << ",\"protection_state\":\"" << (state < 0 ? "unavailable" : names[state]) << "\","
                << "\"provisioned\":" << (state >= UKE_FS_READY && state <= UKE_FS_RUNNING ? "true" : "false")
                << ",\"protected_graph_running\":" << (state == UKE_FS_RUNNING ? "true" : "false")
                << ",\"physical_evidence\":{\"dsp_protection_mode\":\"unverified\","
                << "\"electrical_calibration_and_physical_binding\":\"unverified\","
                << "\"gain_transfer_function\":\"unverified\",\"vi_mapping_scaling_continuity\":\"unverified\","
                << "\"power_limit\":\"unverified\",\"coil_temperature_limit\":\"unverified\","
                << "\"excursion_limit\":\"unverified\",\"fault_response_deadline\":\"unverified\"},"
                << "\"physical_protection_qualified\":false}\n";
            return 2;
        }
        if (status_only || has_control) {
            require_runtime(!apply && !(status_only && has_control));
            Control control(card, true);
            if (has_control) return control.available() ? 0 : 1;
            static constexpr const char *names[] = {"empty", "staging", "ready", "prepared", "running", "fault"};
            const auto state = control.status();
            std::cout << "{\"schema_version\":1,\"state\":\"" << names[state]
                << "\",\"gain_ceiling\":223,\"physical_protection_qualified\":false}\n";
            return 0;
        }
        struct rlimit core{0, 0};
        require_runtime(setrlimit(RLIMIT_CORE, &core) == 0 && prctl(PR_SET_DUMPABLE, 0) == 0);
        // Reject user-created lookalikes and pin the real kernel numid before
        // opening any calibration source. Device removal also fails each write.
        std::unique_ptr<Control> control;
        if (apply) {
            require_runtime(geteuid() == 0);
            control = std::make_unique<Control>(card);
            control->lock();
            if (ensure_loaded) {
                const auto state = control->status();
                if (state >= UKE_FS_READY && state <= UKE_FS_RUNNING) return 0;
                require_runtime(state == UKE_FS_EMPTY);
            }
        }
        auto parameters = generic_parameters(acdb);
        // Refuse to read unit data if the process cannot keep it out of swap.
        require_runtime(mlockall(MCL_CURRENT | MCL_FUTURE) == 0);
        PrivateSession session;
        session.calibration = read_persist_calibration(directory);
        if (apply) {
            load(*control, session, parameters);
        }
        std::cout << (apply ? "Speaker parameters staged; playback still requires the protected kernel graph.\n"
                           : "Read-only calibration consistency and generic DSP data checks passed.\n");
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "uke-speaker-runtime: " << error.what() << '\n';
        return 1;
    }
}
