// Host-only snapshot for a bounded, offline update of an existing filesystem.
#include <sys/stat.h>
#include <sys/xattr.h>
#include <openssl/evp.h>
#include <algorithm>
#include <array>
#include <cerrno>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
static std::string hex(const std::string &s) {
    std::ostringstream o;
    for (unsigned char c : s) o << std::hex << std::setw(2) << std::setfill('0') << unsigned(c);
    return o.str();
}
static std::string digest(const fs::path &p) {
    std::ifstream in(p, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot open " + p.string());
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx || EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) != 1) throw std::runtime_error("Digest init");
    std::array<char, 1048576> b{};
    while (in) { in.read(b.data(), b.size()); if (EVP_DigestUpdate(ctx, b.data(), in.gcount()) != 1) throw std::runtime_error("Digest update"); }
    if (!in.eof()) throw std::runtime_error("Cannot read " + p.string());
    std::array<unsigned char, EVP_MAX_MD_SIZE> out{}; unsigned int n = 0;
    if (EVP_DigestFinal_ex(ctx, out.data(), &n) != 1) throw std::runtime_error("Digest final");
    EVP_MD_CTX_free(ctx);
    return hex(std::string(reinterpret_cast<char *>(out.data()), n));
}
int main(int argc, char **argv) {
    try {
        if (argc != 2) throw std::runtime_error("Usage: inventory ROOT");
        fs::path root = fs::canonical(argv[1]);
        if (root == "/") throw std::runtime_error("Host root refused");
        std::vector<fs::path> paths{root};
        for (const auto &e : fs::recursive_directory_iterator(root)) paths.push_back(e.path());
        std::sort(paths.begin(), paths.end());
        for (const auto &p : paths) {
            std::string rel = p == root ? "." : p.lexically_relative(root).generic_string();
            if (rel.find_first_of("\t\n\r") != std::string::npos) throw std::runtime_error("Unsupported path");
            struct stat st{};
            if (lstat(p.c_str(), &st)) throw std::runtime_error("Cannot stat " + rel);
            std::cout << rel << '\t' << st.st_mode << ':' << st.st_uid << ':' << st.st_gid;
            // Directory timestamps change when their kernel-owned children change.
            if (!S_ISDIR(st.st_mode)) std::cout << ':' << st.st_mtim.tv_sec << ':' << st.st_mtim.tv_nsec;
            if (S_ISREG(st.st_mode)) std::cout << ':' << st.st_size << ':' << digest(p);
            else if (S_ISLNK(st.st_mode)) std::cout << ':' << hex(fs::read_symlink(p).native());
            else if (!S_ISDIR(st.st_mode)) std::cout << ':' << st.st_rdev;
            ssize_t n = llistxattr(p.c_str(), nullptr, 0);
            if (n < 0) throw std::runtime_error("Cannot list xattrs " + rel);
            std::string names(static_cast<size_t>(n), '\0');
            if (llistxattr(p.c_str(), names.data(), names.size()) != n) throw std::runtime_error("Changed xattrs " + rel);
            std::vector<std::string> attrs;
            for (size_t i=0; i<names.size();) { attrs.push_back(names.c_str()+i); i += attrs.back().size()+1; }
            std::sort(attrs.begin(), attrs.end());
            for (const auto &name : attrs) {
                ssize_t len = lgetxattr(p.c_str(), name.c_str(), nullptr, 0);
                if (len < 0) throw std::runtime_error("Cannot read xattr " + rel);
                std::string value(static_cast<size_t>(len), '\0');
                if (lgetxattr(p.c_str(), name.c_str(), value.data(), value.size()) != len) throw std::runtime_error("Changed xattr " + rel);
                std::cout << ':' << hex(name) << '=' << hex(value);
            }
            std::cout << '\n';
        }
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
