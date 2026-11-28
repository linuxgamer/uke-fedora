// SPDX-License-Identifier: GPL-2.0-only
#ifndef UKE_SPEAKER_PERSIST_HPP
#define UKE_SPEAKER_PERSIST_HPP
#include <array>
#include <cerrno>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <unistd.h>
#include "uke-speaker-calibration.hpp"

namespace uke::audio {
class PersistFd {
    int fd_;
public:
    explicit PersistFd(int fd) : fd_(fd) {
        if (fd < 0) throw std::runtime_error("speaker calibration source unavailable");
    }
    PersistFd(const PersistFd &) = delete;
    PersistFd &operator=(const PersistFd &) = delete;
    ~PersistFd() { close(fd_); }
    int get() const { return fd_; }
};
template<size_t Capacity> struct PrivateBytes {
    std::array<uint8_t, Capacity> data{};
    size_t size = 0;
    PrivateBytes() = default;
    PrivateBytes(const PrivateBytes &) = delete;
    PrivateBytes &operator=(const PrivateBytes &) = delete;
    ~PrivateBytes() {
        volatile uint8_t *p = data.data();
        for (size_t i = 0; i < data.size(); ++i) p[i] = 0;
    }
};
template<size_t Capacity> void read_persist_file(int directory, const char *name,
                                               PrivateBytes<Capacity> &output) {
    PersistFd input(openat(directory, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW));
    struct stat before{}, after{};
    struct statvfs mount{};
    require_calibration(fstat(input.get(), &before) == 0 && S_ISREG(before.st_mode) &&
        before.st_size > 0 && uint64_t(before.st_size) <= Capacity);
    require_calibration(fstatvfs(input.get(), &mount) == 0 && (mount.f_flag & ST_RDONLY));
    output.size = size_t(before.st_size);
    size_t offset = 0;
    while (offset < output.size) {
        auto result = pread(input.get(), output.data.data() + offset, output.size - offset, offset);
        if (result < 0 && errno == EINTR) continue;
        require_calibration(result > 0);
        offset += size_t(result);
    }
    require_calibration(fstat(input.get(), &after) == 0 &&
        before.st_dev == after.st_dev && before.st_ino == after.st_ino &&
        before.st_size == after.st_size &&
        before.st_mtim.tv_sec == after.st_mtim.tv_sec && before.st_mtim.tv_nsec == after.st_mtim.tv_nsec &&
        before.st_ctim.tv_sec == after.st_ctim.tv_sec && before.st_ctim.tv_nsec == after.st_ctim.tv_nsec &&
        fstatvfs(input.get(), &mount) == 0 && (mount.f_flag & ST_RDONLY));
}
inline CalibrationSnapshot read_persist_calibration(const char *directory) {
    PersistFd parent(open(directory, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW));
    struct statvfs mount{};
    require_calibration(fstatvfs(parent.get(), &mount) == 0 && (mount.f_flag & ST_RDONLY));
    PrivateBytes<16> binary;
    PrivateBytes<2048> text;
    read_persist_file(parent.get(), "fsalgo_rdc.bin", binary);
    read_persist_file(parent.get(), "fsalgo_rdc.txt", text);
    return parse_calibration({binary.data.data(), binary.size},
        {reinterpret_cast<const char *>(text.data.data()), text.size});
}
} // namespace uke::audio
#endif
