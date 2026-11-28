# SPDX-License-Identifier: GPL-3.0-only
"""Read-only diagnostics streamed to the tablet over SSH, plus a user-triggered tone."""

import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def read(path, default=""):
    try:
        return Path(path).read_text(errors="replace").strip().strip("\0")
    except OSError:
        return default


def command(*args, requires_display=False):
    env = os.environ.copy()
    runtime = Path(f"/run/user/{os.getuid()}")
    if (runtime / "bus").exists():
        env.update(XDG_RUNTIME_DIR=str(runtime), DBUS_SESSION_BUS_ADDRESS=f"unix:path={runtime}/bus")
    display = next((p.name for p in sorted(runtime.glob("wayland-*")) if p.is_socket()), None)
    if display:
        env.update(WAYLAND_DISPLAY=display, QT_QPA_PLATFORM="wayland")
    heading = f"$ {' '.join(map(str, args))}"
    if requires_display and not (env.get("WAYLAND_DISPLAY") or env.get("DISPLAY")):
        return f"{heading}\nSign in on the tablet as this SSH user to collect desktop evidence."
    try:
        run = subprocess.run(args, env=env, text=True, errors="replace", stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=8)
    except OSError as error:
        return f"{heading}\nUnavailable ({error.strerror})"
    except subprocess.TimeoutExpired:
        return f"{heading}\nTimed out"
    output = run.stdout.strip()
    return f"{heading}\n{output or '(no output)'}" + (f"\nExit status {run.returncode}" if run.returncode else "")


def sysfs(pattern, attributes):
    lines = []
    for device in sorted(Path("/sys").glob(pattern)):
        values = [f"{key}={value}" for key in attributes if (value := read(device / key))]
        lines.append(f"{device.relative_to('/sys')}  {'  '.join(values)}")
    return "\n".join(lines) or f"No entries under /sys/{pattern}"


def cpu_ticks():
    counts = [int(n) for n in read("/proc/stat").splitlines()[0].split()[1:9]]
    return sum(counts), counts[3] + counts[4]


def battery_status(device, is_uke):
    status = read(device / "status")
    if is_uke and device.name == "qcom-battmgr-bat" and status == "Charging":
        # Senemos exposes charge-positive current from the Uke gauge.
        try:
            current = int(read(device / "current_now"))
        except ValueError:
            return status
        if current < -100_000:
            return "Discharging (firmware reports Charging)"
    return status


def stats():
    total, idle = cpu_ticks()
    time.sleep(0.2)
    after_total, after_idle = cpu_ticks()
    cpu = 100 * (1 - (after_idle - idle) / max(1, after_total - total))
    memory = dict(re.findall(r"^(MemTotal|MemAvailable):\s+(\d+)", read("/proc/meminfo"), re.M))
    total_mb = int(memory["MemTotal"]) // 1024
    used_mb = total_mb - int(memory["MemAvailable"]) // 1024
    is_uke = "xiaomi,uke" in read("/sys/firmware/devicetree/base/compatible").split("\0")
    battery = [f"{value}% {battery_status(p, is_uke)}" for p in sorted(Path("/sys/class/power_supply").glob("*"))
               if read(p / "type") == "Battery" and (value := read(p / "capacity"))]
    uptime = int(float(read("/proc/uptime").split()[0]))
    return {"CPU": f"{cpu:.0f}%", "Memory": f"{used_mb:,} / {total_mb:,} MiB",
            "Battery": ", ".join(battery) or "No battery reported",
            "Uptime": f"{uptime // 3600}h {uptime % 3600 // 60:02}m",
            "Load": " / ".join(read("/proc/loadavg").split()[:3])}


def graphics():
    kwin = command("qdbus-qt6", "org.kde.KWin", "/KWin", "supportInformation")
    renderer = re.findall(r"^.*(?:renderer|OpenGL vendor|Compositing Type|Driver:).*$", kwin, re.I | re.M)
    return ["\n".join(renderer) if renderer else kwin, command("kscreen-doctor", "-o", requires_display=True),
            command("loginctl", "list-sessions", "--no-pager"),
            sysfs("class/drm/card*-*", ("status", "enabled", "modes")),
            sysfs("class/backlight/*", ("brightness", "actual_brightness", "max_brightness")),
            command("ls", "-l", "/dev/dri"), command("eglinfo", "-B"),
            command("vulkaninfo", "--summary"), command("clinfo", "-l"),
            kernel_logs("adreno|a[67][0-9]{2}|drm|gpu|firmware|backlight|displayport|dsc|vrr", kernel=True)]


def input_devices():
    return [sysfs("class/input/event*/device", ("name", "phys", "capabilities/ev", "capabilities/abs",
                                                "capabilities/sw")),
            command("libinput", "list-devices"), command("localectl", "status"),
            kernel_logs("touchscreen|novatek|nt36532|stylus|pogo|buffyboard|virtual keyboard")]


def audio():
    return [command("wpctl", "status", "--name"), read("/proc/asound/cards", "No ALSA cards file"),
            read("/proc/asound/pcm", "No ALSA PCM devices file"),
            command("systemctl", "--user", "--no-pager", "status", "pipewire", "wireplumber"),
            kernel_logs("soundwire|audio|asoc|adsp|snd_soc|q6afe|amplifier")]


def power():
    return [sysfs("class/power_supply/*", ("type", "present", "online", "status", "capacity", "voltage_now",
                                          "current_now", "power_now", "temp", "usb_type", "voltage_max",
                                          "current_max", "input_current_limit", "charge_counter",
                                          "charge_control_start_threshold", "charge_control_end_threshold")),
            command("upower", "-d"), command("timedatectl", "status"),
            command("chronyc", "tracking"),
            sysfs("class/rtc/*", ("name", "date", "time", "hctosys")),
            sysfs("class/thermal/thermal_zone*", ("type", "temp")),
            sysfs("class/thermal/cooling_device*", ("type", "cur_state", "max_state")),
            sysfs("class/leds/*", ("brightness", "max_brightness", "multi_index", "multi_intensity")),
            sysfs("class/wakeup/*", ("name", "event_count", "wakeup_count")),
            "\n".join(f"{name}: {read('/sys/power/' + name, 'unavailable')}"
                      for name in ("state", "mem_sleep", "disk", "resume")),
            command("swapon", "--show"), read("/sys/kernel/security/lockdown", "Lockdown state unavailable"),
            command("systemd-inhibit", "--list", "--no-pager"),
            command("journalctl", "-b", "-1", "-u", "systemd-logind", "-u", "systemd-suspend.service",
                    "--no-pager", "-o", "short-monotonic", "-n", "35"),
            kernel_logs("battery|charger|power.supply|built-in epoch|rtc|thermal|suspend|hibernat|wakeup")]


def sensors():
    devices = sorted(Path("/sys/bus/iio/devices").glob("iio:device*"))
    channels = [f"{p.name} ({read(p / 'name', 'unknown')}): " +
                ", ".join(attr.name for attr in sorted(p.glob("in_*"))) for p in devices]
    return [command("busctl", "--system", "introspect", "net.hadess.SensorProxy", "/net/hadess/SensorProxy"),
            "\n".join(channels) or "No IIO channels exposed",
            sysfs("class/remoteproc/remoteproc*", ("name", "state")),
            command("systemctl", "--no-pager", "status", "iio-sensor-proxy", "uke-ssc-cache", "uke-ssc-root"),
            kernel_logs(r"ssc|fast.?rpc|iio|accelerometer|proximity|magnet|remoteproc|\b[acw]dsp\b|wcss|wpss|pmic")]


def connectivity():
    return [command("nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"),
            command("rfkill", "list"), command("bluetoothctl", "show"),
            command("kdeconnect-cli", "--list-devices"), command("lsusb", "-t"),
            sysfs("class/typec/*", ("data_role", "power_role", "power_operation_mode", "port_type")),
            sysfs("class/usb_role/*", ("role",)), sysfs("class/udc/*", ("state", "current_speed")),
            sysfs("class/net/*", ("operstate", "speed", "statistics/rx_dropped", "statistics/tx_dropped")),
            sysfs("class/nfc/*", ("uevent",)), sysfs("class/rc/*", ("protocols",)),
            kernel_logs("wlan|wpa_supplicant|NetworkManager|bluetooth|usb|type-c|nfc|infrared|r8152")]


def media():
    return [sysfs("class/video4linux/*", ("name",)), command("v4l2-ctl", "--list-devices"),
            command("vainfo"), kernel_logs("venus|iris|v4l2|codec|camera|camss|eeprom|video")]


def boot_and_storage():
    return [read("/proc/sys/kernel/random/boot_id"), read("/proc/cmdline"),
            command("systemd-analyze", "time"), command("journalctl", "-b", "-u", "uke-slot-success.service", "--no-pager", "-n", "12"),
            command("journalctl", "-b", "-1", "--no-pager", "-n", "25", "-o", "short-monotonic",
                    "-g", "shutting down|unmount|timed out|reboot|powering off"),
            command("findmnt", "-n", "-o", "SOURCE,FSTYPE,OPTIONS", "/"),
            command("lsblk", "-o", "NAME,TYPE,SIZE,FSTYPE,TRAN"),
            command("free", "-m"),
            sysfs("devices/system/cpu/cpufreq/policy*", ("affected_cpus", "scaling_governor", "scaling_min_freq",
                                                        "scaling_max_freq", "scaling_cur_freq")),
            sysfs("class/devfreq/*", ("name", "governor", "cur_freq")),
            sysfs("bus/event_source/devices/*", ("type",)),
            sysfs("bus/platform/drivers/ufshcd-qcom/*/capabilities", ("mcq", "crypto", "write_booster")),
            command("powerprofilesctl", "list"), command("ls", "-ld", "/sys/firmware/efi", "/dev/kvm"),
            kernel_logs(r"ufs|ufshcd|write.?boost|inline.?crypt|mcq|memlat|icc|cpufreq|coresight|kvm|hypervisor|el2")]


def kernel_logs(pattern, *, kernel=False):
    return command("journalctl", *(("-k",) if kernel else ()), "-b", "--no-pager",
                   "-o", "short-monotonic", "-n", "60", "-g", pattern)


def overview():
    return [command("uname", "-r"), command("date", "--iso-8601=seconds"),
            read("/etc/os-release"), json.dumps(stats(), ensure_ascii=False),
            command("systemctl", "--no-pager", "--failed")]


def tone():
    rate = 48000
    with tempfile.TemporaryDirectory(prefix="uke-tone-") as directory:
        path = Path(directory) / "test.wav"
        with wave.open(str(path), "wb") as output:
            output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            frames = (int(2300 * math.sin(2 * math.pi * 440 * i / rate)
                          * min(i / 1000, (36000 - i) / 1000, 1)) for i in range(36000))
            output.writeframes(b"".join(struct.pack("<h", frame) for frame in frames))
        return [command("pw-play", str(path)), "Record whether the tone was audible in the tester notes."]


CHECKS = {
    "overview": ("Overview", overview),
    "boot": ("Boot, CPU & storage", boot_and_storage),
    "graphics": ("Graphics & brightness", graphics),
    "input": ("Touch & input", input_devices),
    "network": ("Networking & USB", connectivity),
    "sensors": ("Rotation & sensors", sensors),
    "audio": ("Audio", audio),
    "media": ("Cameras & video", media),
    "power": ("Battery & clock", power),
}


def main():
    request = sys.argv[1]
    if request == "Live stats":
        print(json.dumps(stats()))
        return
    checks = {label: run for label, run in CHECKS.values()}
    if request != "All checks":
        checks = {request: tone if request == "Play test tone" else checks[request]}
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [(label, workers.submit(run)) for label, run in checks.items()]
        for label, result in futures:
            print(f"== {label} ==\n\n" + "\n\n".join(result.result()) + "\n")


if __name__ == "__main__":
    main()
