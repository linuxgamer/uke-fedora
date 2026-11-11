# Developing the Uke Fedora port

This is the first-hour guide for someone who wants to change the port, not only
install it. The rules that apply to every change are in [AGENTS.md](../AGENTS.md);
this page covers the environment, the checks and the git flow.

The umbrella repository holds documentation, the upstream pin and tooling. The
port itself lives in three submodule forks; almost every code change happens in
one of them.

## What you need

| Area | Requirements |
| --- | --- |
| Base | Linux host, `git`, `bash`, `python3`, `sha256sum`, network access |
| Docs-only work | The base tools; no containers or compilers |
| Source checks | `jq`, `rpm` and `rpmspec`, `dtc`, `clang`/`clang++` (kernel contracts) |
| Builder CI parity | `shellcheck`, `zstd`, `zip`, `unzip`, `e2fsprogs`, `ripgrep`, `make` |
| Image build | Docker or Podman, `avbtool`, `jq`, `g++`, `zstd`, and free disk |

Run the preflight and let it tell you what is missing:

```sh
tools/check-dev-env.sh          # tools needed by the source checks and builds
tools/check-dev-env.sh --quick  # clone shape only, enough for docs work
```

The script prints the missing tool and where it is needed. It does not install
anything. Kernel contract checks and image builds need the Fedora-era toolchain
(`rpm`, `rpmspec`, `dtc`, `clang`); a clean Arch or Ubuntu host usually has none
of them, and the checks fail with a misleading message until they are installed.
See [Troubleshooting](#troubleshooting).

Disk: plan at least 25 GiB for a kernel build. An image build additionally keeps
root filesystems and image pairs under `build/`; check with `df -h .` before a
first run.

## Get the tree

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
cd uke-fedora
git submodule update --init --recursive
```

A full clone is about 240 MiB because the kernel fork carries source archives.
The submodules are checked out at the commits recorded by the umbrella
(gitlinks). They are usually detached commits; that is normal and not a sign of
a broken clone. Do not "fix" a submodule by checking out its `main` unless you
intend to move the gitlink.

```sh
git status
git submodule status    # '+' means the worktree is ahead of the recorded gitlink
```

## Repository map

| Path | Owner | Change it when |
| --- | --- | --- |
| `README.md`, `INSTALL.md` | umbrella | User-visible facts, hardware table, flashing |
| `docs/` | umbrella | Developer documentation and status |
| `AGENTS.md` | umbrella | Rules for contributors and AI agents |
| `tools/` | umbrella | Host tooling for docs, sync and COPR |
| `upstream.lock` | umbrella | Only after a reviewed upstream sync |
| `senemos-uke-kernel/` | fork | Kernel, device trees, kernel packaging |
| `uke-fedora-builder/` | fork | Image recipes, rootfs, release packaging |
| `uke-linux-hardware-support/` | fork | Packages, boot integration, firmware rules |

`private/`, `build/` and `artifacts/` are local and gitignored. Never link to
them from a published document. Root-level `/tests`, `/scripts` and `/manifests`
are also gitignored; repository tooling belongs in `tools/`.

## Checks

Run the checks that cover your change. The commands below are the documented
ones; if a command fails, read the failure before changing code.

### Documentation checks

```sh
tools/check-docs.sh
```

Checks every relative link in the published Markdown against the tracked tree.
It fails on a link into a submodule (GitHub renders such links as 404), on a
link into `private/` or `build/`, and on a target that does not exist. Run it for
every documentation change; it is not wired into CI yet (backlog B14).

### Kernel source checks

```sh
make -C senemos-uke-kernel check-pins   # fast, must pass
make -C senemos-uke-kernel validate     # slow, needs the host toolchain
```

`check-pins` verifies the active manifest digests. `validate` runs the source
contracts and needs `rpm`/`rpmspec`, `dtc` and `clang`/`clang++`; without them
one of the last contracts exits non-zero **without printing the failing test**
(`make` reports only `Makefile:17: validate`). If that happens, run
`tools/check-dev-env.sh` and install what it lists, or run the contracts one by
one from `senemos-uke-kernel/Makefile` to see the exact failure.

### Hardware-support checks

```sh
make -C uke-linux-hardware-support validate
```

Checks package metadata, source locks, schemas and service/udev contracts. It
does not need containers and is fast enough for every change.

### Builder checks

The documented quick gate is a syntax check:

```sh
(cd uke-fedora-builder && bash -n build-images.sh build-rootfs.sh src/image/*.sh)
```

CI runs more: `shellcheck` plus the full contract suite from
[`source-contracts.yml`](https://github.com/linuxgamer/uke-fedora-builder/blob/main/.github/workflows/source-contracts.yml).
There is no local one-shot runner yet (backlog B12). For a builder change,
install `shellcheck` and run the workflow commands manually before opening a
pull request, or state in the pull request which checks you did not run.

### Sync checks

```sh
tools/sync-upstream.sh status   # pin, local position, submodule drift
tools/sync-upstream.sh verify   # policy checks on the current branch
```

Both are read-only, but `verify` refuses a dirty working tree: run it after the
change is committed (or in a clean worktree). The sync model is described in
[UPSTREAM.md](UPSTREAM.md).

## Build an image

From the umbrella:

```sh
./uke-fedora-builder/build-images.sh --cross-kernel --profiles kde,gnome \
    --output build/images
```

- `--profiles` selects a subset. Without it, all five profiles (tty, kde,
  gnome, phosh, plasma-mobile) are built; Phosh and Plasma Mobile are not
  device-tested.
- `--cross-kernel` is for x86_64 hosts: the ARM64 kernel is compiled with the
  host Clang instead of emulation. Omit it on an ARM64 host.
- Requirements and cache behaviour:
  [BUILDING](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILDING.md)
  and [BUILD-CACHE](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILD-CACHE.md).
- Progress and cancellation: add `--status` / `--stop` with the same `--output`.
- A build is usable only when `status.json` says `complete` and
  `audit-report.txt` reports no failures. A successful build is not a boot test.

Builds write only under `build/`. Do not run a second build into the same output
directory and do not kill a build you did not start. The builder never flashes a
device; flashing and the on-device smoke test are manual steps in
[RELEASE.md](RELEASE.md).

## Kernel-only build

For kernel development without an image:

```sh
cd senemos-uke-kernel
./senemos.sh --help
./senemos.sh --build 7.3.1 --distro=fedora --test
```

`senemos.sh` prepares host prerequisites and builds in an isolated Fedora
toolchain; it may install host packages and needs about 25 GiB free. Full
instructions and supported hosts:
[BUILDING.md](https://github.com/linuxgamer/senemos-uke-kernel-mainline/blob/main/docs/BUILDING.md).

## Git flow and pull requests

### Umbrella changes (docs, tools, pins)

1. Branch from `main`, for example `docs/developing-guide`.
2. Edit, then run `tools/check-docs.sh` and any check the change touches.
3. Commit in English with a focused message; explain what changed and why.
4. Open a pull request against `linuxgamer/uke-fedora:main`. The umbrella has no
   pull-request CI today: the only workflow is the manual image build. State in
   the pull request which local checks you ran.
5. A gitlink change is a separate pull request and must name the component
   commit it points to.

### Component changes

1. Work in the component repository (`senemos-uke-kernel-mainline`,
   `uke-fedora-builder` or `uke-linux-hardware-support`), not in the umbrella
   copy.
2. Branch, commit and open the pull request in that component repository. The
   component CI runs there (kernel and builder `source-contracts`).
3. Run the component checks listed above in the component tree.
4. After the component change is accepted, the umbrella updates the gitlink.
   Do not include component commits in an umbrella pull request.

Every pull request should answer: what changed, why, what was tested (exact
commands and results), what was not tested, and whether a device or a submodule
pointer is involved. The template in `.github/PULL_REQUEST_TEMPLATE.md` asks for
the same fields.

### What not to do

- Do not rewrite a published tag or release asset.
- Do not move a gitlink without naming the component commit and what was tested.
- Do not commit secrets, private logs, serial numbers, calibration or OEM blobs.
- Do not flash, repartition, switch slots or re-lock the bootloader as part of a
  code change.

## Missing evidence paths

Some component `AGENTS.md` files still point at material that the upstream sync
policy removes from this fork. The paths below do **not** exist in a clean clone:

| Missing path | Where it is referenced | Use instead |
| --- | --- | --- |
| `senemos-uke-kernel/referances/README.md` | kernel `AGENTS.md` | The public source archives under `referances/releases/`, [UPSTREAM.md](UPSTREAM.md) and the kernel README |
| `uke-linux-docs/docs/DONOR-POLICY.md` | kernel `AGENTS.md` | The hardware integration policy in [CONTRIBUTING.md](CONTRIBUTING.md) and the donor rules in [UPSTREAM.md](UPSTREAM.md) |
| `uke-linux-hardware-support/docs/research/ACCESSORY-LAB.md` | hardware `AGENTS.md` | The hardware repo's `docs/lessons/` directory |
| `uke-linux-hardware-support/docs/testing/ACCESSORY-TEST-PLAN.md` | hardware `AGENTS.md` | The hardware repo's `docs/lessons/` directory |

This is a known documentation bug (backlog B15). If a rule points at a path that
does not exist, say so in your change and do not invent the missing evidence.
The rules themselves live in the component repositories and must be fixed there.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `make -C senemos-uke-kernel validate` fails with only `Makefile:17` | A contract failed silently. Run `tools/check-dev-env.sh`; the usual cause is missing `rpm`, `rpmspec`, `dtc` or `clang`. |
| `tools/check-docs.sh` reports a link into a submodule | GitHub returns 404 for paths inside a submodule. Link to the component repository URL. |
| `git submodule status` shows `-` or a submodule directory is empty | Run `git submodule update --init --recursive`. |
| `git submodule status` shows `+` | The component worktree is ahead of the umbrella gitlink. That is normal during development; update the gitlink only on purpose. |
| `git status` shows a submodule as modified but you changed nothing | The component checkout moved. Run `git -C <component> status`; do not discard another agent's work. |
| `bash -n` passes but the builder CI fails in `shellcheck` | `bash -n` is syntax only. Install `shellcheck` and run the workflow commands. |
| A component rule points at a missing file | See [Missing evidence paths](#missing-evidence-paths); do not invent the file. |

## Where to start

After the first clone and a passing `tools/check-dev-env.sh --quick`, look at
[docs/BACKLOG.md](BACKLOG.md). Items without a device or COPR dependency are the
best first tasks; documentation and tooling work is marked `P2` unless it
unblocks something else. The `P0` items need the maintainer's COPR access or the
tablet.

## Status and handoff

- Current facts: [STATE.md](STATE.md).
- Work queue: [BACKLOG.md](BACKLOG.md).
- Upstream pin and rebase model: [UPSTREAM.md](UPSTREAM.md).
- Release process: [RELEASE.md](RELEASE.md).
- Evidence per hardware block: [HARDWARE.md](HARDWARE.md).
