# SPDX-License-Identifier: GPL-3.0-only
"""Desktop and headless diagnostics for uke-fedora."""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except ImportError:
    tk = None

from hardware_checks import FEATURES, UPSTREAM
from tablet_probe import CHECKS


PROBE = Path(__file__).with_name("tablet_probe.py")
KEY = Path.home() / ".ssh" / "uke-debug-ed25519"
PUBLIC_KEY = KEY.with_suffix(".pub")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
METRICS = ("CPU", "Memory", "Battery", "Uptime", "Load")
CHECK_REQUESTS = {"all": "All checks", **{key: label for key, (label, _) in CHECKS.items()},
                  "tone": "Play test tone"}
RESULTS = ("Not tested", "Pass", "Partial", "Fail", "Blocked")


def ssh(target, port, *, batch=False):
    user, separator, host = target.strip().partition("@")
    if not separator or not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*", user):
        raise ValueError("Enter the tablet login as user@ip-address.")
    if not re.fullmatch(r"[a-zA-Z0-9:][a-zA-Z0-9.:-]*", host):
        raise ValueError("Enter a valid tablet IP address or hostname.")
    if not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ValueError("SSH port must be between 1 and 65535.")
    client = shutil.which("ssh")
    if not client:
        raise OSError("OpenSSH Client (ssh) is missing from PATH.")
    args = [client, "-o", "ConnectTimeout=5", "-o", "ServerAliveInterval=5",
            "-o", "ServerAliveCountMax=2", "-p", port, "-l", user]
    if KEY.is_file():
        args += ["-i", str(KEY), "-o", "IdentitiesOnly=yes"]
    if batch:
        args += ["-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes"]
    else:
        args += ["-t", "-o", "StrictHostKeyChecking=ask"]
    return [*args, "--", host]


def fetch(target, port, request):
    limit = 180 if request == "All checks" else 105
    if request == "Live stats":
        limit = 12
    run = subprocess.run([*ssh(target, port, batch=True), "python3 - " + shlex.quote(request)],
                         input=PROBE.read_text(encoding="utf-8"), text=True, encoding="utf-8",
                         errors="replace", capture_output=True, timeout=limit, creationflags=NO_WINDOW)
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or run.stdout.strip() or f"SSH exited with status {run.returncode}.")
    return json.loads(run.stdout) if request == "Live stats" else run.stdout


def capture(args, timeout=15, *, cwd=None):
    run = subprocess.run(args, text=True, encoding="utf-8", errors="replace", capture_output=True,
                         timeout=timeout, cwd=cwd, creationflags=NO_WINDOW)
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or run.stdout.strip() or f"Exit status {run.returncode}.")
    return run.stdout


def adb_devices():
    adb = shutil.which("adb")
    if not adb:
        raise OSError("Android Platform Tools (adb) are missing from PATH.")
    rows = capture([adb, "devices"]).splitlines()[1:]
    devices = []
    for row in rows:
        if fields := row.split(maxsplit=2):
            if len(fields) >= 2:
                devices.append({"serial": fields[0], "state": fields[1]})
    return adb, devices


def recovery_adb():
    adb, devices = adb_devices()
    recovery = [device["serial"] for device in devices if device["state"] == "recovery"]
    if len(recovery) != 1:
        raise RuntimeError("Connect one tablet running TWRP over USB.")
    return [adb, "-s", recovery[0]]


def collect_recovery(destination):
    adb = recovery_adb()
    try:
        capture([*adb, "shell", "test", "-d", "/data/var/log/journal"])
    except RuntimeError as error:
        raise RuntimeError("Fedora journal unavailable. Check whether TWRP has mounted /data.") from error
    directory = Path(destination).resolve() / f"uke-recovery-{datetime.now():%Y%m%d-%H%M%S-%f}"
    directory.mkdir(parents=True)
    # Windows ADB can truncate directory names when passed a non-ASCII destination.
    capture([*adb, "pull", "/data/var/log/journal", "journal"], timeout=180, cwd=directory)
    result = {"directory": str(directory), "journal": str(directory / "journal"),
              "pstore": str(directory / "pstore"), "warning": None}
    try:
        capture([*adb, "pull", "/sys/fs/pstore", "pstore"], timeout=30, cwd=directory)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        result.update(pstore=None, warning=f"Could not copy pstore. {error}")
    return result


def recovery_report(destination):
    result = collect_recovery(destination)
    message = f"Recovery journal saved in {result['directory']}"
    if result["warning"]:
        message += f"\n{result['warning']}"
    return message


def terminal(args):
    if os.name == "nt":
        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return
    for name, flags in (("x-terminal-emulator", ["-e"]), ("konsole", ["-e"]),
                        ("gnome-terminal", ["--"]), ("xterm", ["-e"])):
        if executable := shutil.which(name):
            subprocess.Popen([executable, *flags, *args])
            return
    raise OSError("No supported desktop terminal found.")


def authorize(target, port):
    ssh(target, port)
    if not KEY.is_file():
        generator = shutil.which("ssh-keygen")
        if not generator:
            raise OSError("OpenSSH ssh-keygen is missing from PATH.")
        if PUBLIC_KEY.exists():
            raise OSError(f"Public key exists without its private key at {KEY}.")
        KEY.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([generator, "-q", "-t", "ed25519", "-N", "", "-C", "uke-debug", "-f", str(KEY)],
                       check=True, capture_output=True, creationflags=NO_WINDOW)
    if not PUBLIC_KEY.is_file():
        raise OSError(f"Public key missing at {PUBLIC_KEY}.")
    key = PUBLIC_KEY.read_text(encoding="utf-8").strip()
    remote = f"""from pathlib import Path
path = Path.home() / '.ssh' / 'authorized_keys'
path.parent.mkdir(mode=0o700, exist_ok=True)
key = {key!r}
previous = path.read_text() if path.exists() else ''
if key not in previous.splitlines():
    with path.open('a') as file:
        if previous and not previous.endswith('\\n'):
            file.write('\\n')
        file.write(key + '\\n')
path.chmod(0o600)
"""
    command = "python3 -c " + shlex.quote(remote)
    executable = Path(sys.executable)
    if os.name == "nt" and executable.name.lower() == "pythonw.exe":
        executable = executable.with_name("python.exe")
    terminal([str(executable), str(Path(__file__).resolve()), "--authorize-terminal", *ssh(target, port), command])


class HardwareChecklist:
    def __init__(self, frame, run_evidence):
        self.features = {key: (group, label, steps) for key, group, label, steps in FEATURES}
        self.results = {}
        self.current = ""
        self.steps = tk.StringVar(value="Select a feature to see how to test it.")
        self.status = tk.StringVar(value=RESULTS[0])
        self.note = tk.StringVar()

        listing = ttk.Frame(frame)
        listing.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(listing, columns=("group", "status"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Feature")
        self.tree.heading("group", text="Diagnostics")
        self.tree.heading("status", text="Result")
        self.tree.column("#0", width=245)
        self.tree.column("group", width=155)
        self.tree.column("status", width=90, stretch=False)
        scroll = ttk.Scrollbar(listing, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        for key, (group, label, _) in self.features.items():
            self.tree.insert("", "end", iid=key, text=label, values=(CHECK_REQUESTS[group], RESULTS[0]))
        self.tree.bind("<<TreeviewSelect>>", self.select)

        ttk.Label(frame, textvariable=self.steps, wraplength=740).pack(anchor="w", pady=6)
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        self.evidence = ttk.Button(controls, text="Collect evidence", state="disabled",
                                   command=lambda: run_evidence(self.features[self.current][0]))
        self.evidence.pack(side="left")
        ttk.Combobox(controls, textvariable=self.status, state="readonly", values=RESULTS,
                     width=11).pack(side="left", padx=6)
        ttk.Label(controls, text="Observation").pack(side="left", padx=(0, 5))
        ttk.Entry(controls, textvariable=self.note).pack(side="left", fill="x", expand=True)
        self.status.trace_add("write", self.record)
        self.note.trace_add("write", self.record)
        self.tree.selection_set(FEATURES[0][0])

    def select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        key = selection[0]
        self.current = ""
        status, note = self.results.get(key, (RESULTS[0], ""))
        self.status.set(status)
        self.note.set(note)
        self.steps.set(self.features[key][2])
        self.current = key
        self.evidence.configure(state="normal")

    def record(self, *_args):
        if self.current:
            status = self.status.get()
            self.results[self.current] = (status, self.note.get().strip())
            self.tree.set(self.current, "status", status)

    def report(self):
        lines = ["Hardware checklist", f"Reference: {UPSTREAM}"]
        for key, (_, label, _) in self.features.items():
            status, note = self.results.get(key, (RESULTS[0], ""))
            lines.append(f"{status} | {label}" + (f" | {note}" if note else ""))
        return "\n".join(lines)


class Harness:
    def __init__(self, window, target=""):
        self.window = window
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.endpoint = None
        self.live_timer = None
        self.target = tk.StringVar(value=target)
        self.port = tk.StringVar(value="22")
        self.status = tk.StringVar(value="Enter your Fedora login and tablet IP address.")
        self.metric = {name: tk.StringVar(value="—") for name in METRICS}
        self.reports = []

        window.title("Uke Debug")
        window.geometry("1000x690")
        window.minsize(820, 540)
        window.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(window, padding=14)
        frame.pack(fill="both", expand=True)
        connection = ttk.Frame(frame)
        connection.pack(fill="x")
        ttk.Label(connection, text="Tablet").pack(side="left")
        ttk.Entry(connection, textvariable=self.target, width=28).pack(side="left", padx=6)
        ttk.Label(connection, text="Port").pack(side="left")
        ttk.Entry(connection, textvariable=self.port, width=6).pack(side="left", padx=6)
        ttk.Button(connection, text="Authorize key…", command=self.enroll).pack(side="left", padx=3)
        ttk.Button(connection, text="Open shell", command=self.shell).pack(side="left", padx=3)
        self.live = ttk.Button(connection, text="Connect", command=self.toggle_live)
        self.live.pack(side="left", padx=3)
        ttk.Label(frame, textvariable=self.status, wraplength=780).pack(fill="x", pady=(5, 12))

        dashboard = ttk.Frame(frame)
        dashboard.pack(fill="x")
        for column, (name, value) in enumerate(self.metric.items()):
            dashboard.columnconfigure(column, weight=1, uniform="metric")
            card = ttk.LabelFrame(dashboard, text=name, padding=(8, 5))
            card.grid(row=0, column=column, sticky="ew", padx=(0, 5))
            ttk.Label(card, textvariable=value, wraplength=140).pack(anchor="w")

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(12, 8))
        self.selection = tk.StringVar(value="All checks")
        ttk.Combobox(controls, textvariable=self.selection, state="readonly", width=23,
                     values=tuple(label for key, label in CHECK_REQUESTS.items() if key != "tone")).pack(side="left")
        self.run = ttk.Button(controls, text="Run diagnostics", command=lambda: self.start(self.selection.get()))
        self.run.pack(side="left", padx=6)
        self.tone = ttk.Button(controls, text="Play test tone", command=lambda: self.start("Play test tone"))
        self.tone.pack(side="left")
        ttk.Button(controls, text="TWRP shell", command=self.recovery_shell).pack(side="left", padx=(8, 3))
        self.recovery = ttk.Button(controls, text="Pull TWRP logs…", command=self.recovery_logs)
        self.recovery.pack(side="left", padx=3)
        ttk.Button(controls, text="Save report…", command=self.save).pack(side="right")

        tabs = ttk.Notebook(frame)
        tabs.pack(fill="both", expand=True)
        output = ttk.Frame(tabs, padding=5)
        checklist = ttk.Frame(tabs, padding=5)
        notes = ttk.Frame(tabs, padding=5)
        tabs.add(output, text="Diagnostics")
        tabs.add(checklist, text="Hardware checklist")
        tabs.add(notes, text="Tester notes")
        self.checklist = HardwareChecklist(checklist, lambda group: self.start(CHECK_REQUESTS[group]))
        self.tabs, self.diagnostics = tabs, output
        self.output = ScrolledText(output, wrap="none", state="disabled")
        self.output.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(output, orient="horizontal", command=self.output.xview)
        scroll.pack(fill="x")
        self.output.configure(xscrollcommand=scroll.set)
        self.notes = ScrolledText(notes, wrap="word")
        self.notes.pack(fill="both", expand=True)

    def address(self):
        return self.target.get().strip(), self.port.get().strip()

    def enroll(self):
        try:
            authorize(*self.address())
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            messagebox.showerror("Authorize key", str(error), parent=self.window)
        else:
            self.status.set("Compare the SSH fingerprint in the terminal with the tablet’s. Connect after authorization succeeds.")

    def shell(self):
        try:
            terminal(ssh(*self.address()))
        except (OSError, ValueError) as error:
            messagebox.showerror("Open shell", str(error), parent=self.window)

    def recovery_shell(self):
        try:
            terminal([*recovery_adb(), "shell"])
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            messagebox.showerror("TWRP shell", str(error), parent=self.window)

    def recovery_logs(self):
        if self.pending is not None:
            return
        destination = filedialog.askdirectory(parent=self.window, title="Save TWRP capture in…")
        if destination and self.pending is None:
            self.submit("TWRP capture", ("TWRP over USB", ""), recovery_report, destination)

    def toggle_live(self):
        if self.endpoint is not None:
            self.endpoint = None
            self.cancel_timer()
            self.live.configure(text="Connect")
            self.reset_stats()
            self.status.set("Live stats paused.")
            return
        endpoint = self.address()
        try:
            ssh(*endpoint, batch=True)
        except (OSError, ValueError) as error:
            self.status.set(str(error))
            return
        self.endpoint = endpoint
        self.live.configure(text="Pause live")
        self.start("Live stats")

    def reset_stats(self):
        for value in self.metric.values():
            value.set("—")

    def start(self, request):
        if self.pending is not None:
            return
        endpoint = self.endpoint if request == "Live stats" else self.address()
        if endpoint is None:
            return
        if request != "Live stats":
            self.tabs.select(self.diagnostics)
        self.submit(request, endpoint, fetch, *endpoint, request)

    def submit(self, request, endpoint, function, *args):
        self.cancel_timer()
        self.pending = (request, endpoint, self.executor.submit(function, *args))
        self.run.state(["disabled"])
        self.tone.state(["disabled"])
        self.recovery.state(["disabled"])
        if request != "Live stats":
            self.status.set(f"Running {request.lower()} on {endpoint[0]}…")
        self.window.after(100, self.finish)

    def finish(self):
        request, endpoint, future = self.pending
        if not future.done():
            self.window.after(100, self.finish)
            return
        self.pending = None
        self.run.state(["!disabled"])
        self.tone.state(["!disabled"])
        self.recovery.state(["!disabled"])
        if request == "Live stats" and endpoint != self.endpoint:
            self.schedule_live()
            return
        try:
            result = future.result()
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            detail = str(error).splitlines()[0]
            if request == "Live stats":
                self.endpoint = None
                self.live.configure(text="Connect")
                self.reset_stats()
            self.status.set(f"{endpoint[0]} unavailable. {detail}")
            if request != "Live stats":
                self.show(f"{request} · {endpoint[0]}\n\n{error}\n")
        else:
            if request == "Live stats":
                for name, value in self.metric.items():
                    value.set(result.get(name, "—"))
                self.status.set(f"Connected to {endpoint[0]} · live stats every 5 seconds")
            else:
                stamp = datetime.now().astimezone().isoformat(timespec="seconds")
                self.show(f"{request} · {endpoint[0]} · {stamp}\n\n{result}")
                self.status.set(f"{request} finished on {endpoint[0]}.")
        self.schedule_live()

    def schedule_live(self):
        if self.endpoint is not None:
            self.live_timer = self.window.after(5000, self.poll_live)

    def poll_live(self):
        self.live_timer = None
        self.start("Live stats")

    def cancel_timer(self):
        if self.live_timer is not None:
            self.window.after_cancel(self.live_timer)
            self.live_timer = None

    def show(self, text):
        self.reports.append(text)
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def save(self):
        default = Path(__file__).resolve().parents[1] / "private"
        destination = filedialog.asksaveasfilename(parent=self.window, initialdir=default if default.is_dir() else None,
                                                    initialfile=f"uke-debug-{datetime.now():%Y%m%d-%H%M%S}.txt",
                                                    defaultextension=".txt", filetypes=[("Text report", "*.txt")])
        if not destination:
            return
        notes = self.notes.get("1.0", "end-1c").strip()
        try:
            Path(destination).write_text("\n\n".join([f"Tester notes\n{notes}", self.checklist.report(), *self.reports]) + "\n",
                                         encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Save report", str(error), parent=self.window)
        else:
            self.status.set(f"Saved {destination}")

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.window.destroy()


def headless(args):
    try:
        if args.action in ("stats", "check", "ssh-exec") and not args.target:
            raise ValueError("Pass --target user@address before the command.")
        if args.action == "devices":
            return {"devices": adb_devices()[1]}
        if args.action == "coverage":
            return {"reference": UPSTREAM,
                    "features": [{"id": key, "check": group, "feature": label, "steps": steps}
                                 for key, group, label, steps in FEATURES]}
        if args.action in ("serial-check", "serial-lan-recover"):
            from serial_probe import detect_port, fetch_serial, recover_lan

            if args.action == "serial-check" and args.output and args.output.exists():
                raise ValueError(f"Capture already exists: {args.output}")
            device = detect_port() if args.device == "auto" else args.device
            if args.action == "serial-lan-recover":
                return {"device": device, **recover_lan(device, args.user, args.pc_address)}
            report = fetch_serial(device, args.user, CHECK_REQUESTS[args.check], PROBE.read_bytes())
            if args.output:
                with args.output.open("x", encoding="utf-8") as destination:
                    destination.write(report)
                return {"device": device, "path": str(args.output.resolve())}
            return {"device": device, "check": args.check, "report": report}
        if args.action == "twrp-pull":
            return collect_recovery(args.destination)
        if args.action == "stats":
            return {"target": args.target, "stats": fetch(args.target, args.port, "Live stats")}
        if args.action == "check":
            return {"target": args.target, "check": args.check,
                    "report": fetch(args.target, args.port, CHECK_REQUESTS[args.check])}

        if not 1 <= args.timeout <= 600:
            raise ValueError("Timeout must be between 1 and 600 seconds.")
        if args.action == "ssh-exec":
            command = [*ssh(args.target, args.port, batch=True), args.command]
        else:
            command = [*recovery_adb(), "shell", "-T", args.command]
        result = subprocess.run(command, stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                                errors="replace", capture_output=True, timeout=args.timeout,
                                creationflags=NO_WINDOW)
        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"error": f"Command timed out after {error.timeout} seconds."}
    except (OSError, RuntimeError, ValueError) as error:
        return {"error": str(error)}


def main():
    if sys.argv[1:2] == ["--authorize-terminal"]:
        result = subprocess.run(sys.argv[2:])
        print("\nKey authorized. Return to Uke Debug and click Connect." if not result.returncode
              else f"\nAuthorization failed (SSH exit {result.returncode}).")
        input("Press Enter to close.")
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="", help="SSH login as user@address")
    parser.add_argument("--port", default="22", help="SSH port")
    actions = parser.add_subparsers(dest="action", help="headless commands with JSON output")
    actions.add_parser("devices", help="list devices visible over ADB")
    actions.add_parser("coverage", help="list hardware test instructions and diagnostic commands")
    actions.add_parser("stats", help="read live tablet metrics over SSH")
    check = actions.add_parser("check", help="run diagnostics over SSH")
    check.add_argument("check", nargs="?", default="all", choices=CHECK_REQUESTS)
    serial = actions.add_parser("serial-check", help="run diagnostics using Fedora's USB serial login")
    serial.add_argument("device", help="auto, or an explicit serial device such as COM3 or /dev/ttyACM0")
    serial.add_argument("user", help="Fedora login name")
    serial.add_argument("check", nargs="?", default="all", choices=CHECK_REQUESTS)
    serial.add_argument("--output", type=Path, help="save the capture to a new local file")
    recover = actions.add_parser("serial-lan-recover", help="send a Wi-Fi LAN recovery probe to the PC over USB")
    recover.add_argument("device", help="auto, or an explicit serial device such as COM3 or /dev/ttyACM0")
    recover.add_argument("user", help="Fedora login name")
    recover.add_argument("pc_address", help="the PC's Wi-Fi IPv4 address")
    for name, transport in (("ssh-exec", "SSH"), ("twrp-exec", "TWRP over ADB")):
        command = actions.add_parser(name, help=f"run a non-interactive tablet command via {transport}")
        command.add_argument("--timeout", type=int, default=30, help="timeout in seconds")
        command.add_argument("command", help="one shell command string")
    pull = actions.add_parser("twrp-pull", help="copy the Fedora journal and pstore from TWRP")
    pull.add_argument("destination", type=Path, help="parent directory for the new capture")
    args = parser.parse_args()
    if args.action:
        result = headless(args)
        print(json.dumps(result))
        return int("error" in result or result.get("exit_code", 0) != 0)
    if tk is None:
        parser.error("The GUI needs Python with Tk. Use a headless command or install Tk.")
    window = tk.Tk()
    app = Harness(window, args.target)
    app.port.set(args.port)
    window.mainloop()


if __name__ == "__main__":
    sys.exit(main())
