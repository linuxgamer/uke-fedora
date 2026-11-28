# Uke Debug command line

## Automation and coding agents

Run a subcommand from the checkout to use the same diagnostics without opening Tk. For SSH, authorize a key in the GUI first and verify the tablet's host fingerprint. Supply the tablet address for each SSH command.

```text
python extra/uke_debug.py devices
python extra/uke_debug.py coverage
python extra/uke_debug.py --target user@192.0.2.1 stats
python extra/uke_debug.py --target user@192.0.2.1 check graphics
python extra/uke_debug.py --target user@192.0.2.1 ssh-exec "uname -r"
python extra/uke_debug.py twrp-exec "ls /data/var/log/journal"
python extra/uke_debug.py twrp-pull private/bootlogs
```

Each command writes one JSON object to stdout. `coverage` works offline and returns stable feature IDs, physical test steps, and the `check` category to run for evidence. `stats` returns metrics, `check` returns a diagnostic report, and `twrp-pull` returns absolute capture paths. Shell commands return `stdout`, `stderr`, and `exit_code`. Connection or tool errors appear in `error` and produce a nonzero host exit. `check --help` lists the categories. `twrp-exec` and `twrp-pull` require exactly one connected recovery device and use USB when SSH is unreachable.
