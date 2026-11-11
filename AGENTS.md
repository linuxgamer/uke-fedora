# Uke Fedora — contributor and AI-agent rules

This is the entry point for anyone, human or AI, who changes this repository.
It is published with the project, so keep it true for a clean clone. Component
rules live in `<component>/AGENTS.md`; they extend this file, they do not
replace it.

If a document and a fresh command disagree, the command wins. Fix the document.

## What this repository is

The umbrella repository for the Fedora 44 port to Xiaomi Pad 7 and POCO Pad X1
(`uke`, SM7675). It holds user and developer documentation, the upstream pin and
sync tooling, and three submodule forks:

| Path | Repository | What changes there |
| --- | --- | --- |
| `senemos-uke-kernel/` | [senemos-uke-kernel-mainline](https://github.com/linuxgamer/senemos-uke-kernel-mainline) | Kernel, device trees, kernel RPMs |
| `uke-fedora-builder/` | [uke-fedora-builder](https://github.com/linuxgamer/uke-fedora-builder) | Image recipes, rootfs, packaging |
| `uke-linux-hardware-support/` | [uke-linux-hardware-support](https://github.com/linuxgamer/uke-linux-hardware-support) | Device packages, boot integration, firmware payload rules |

`private/`, `build/` and `artifacts/` are local and gitignored. Never link to
them from published documents.

## Read order for a new session

1. [README.md](README.md) — what the project is and what hardware works.
2. [docs/DEVELOPING.md](docs/DEVELOPING.md) — environment, checks, contribution flow.
3. [docs/STATE.md](docs/STATE.md) — facts as of the last handoff.
4. [docs/BACKLOG.md](docs/BACKLOG.md) — ordered work with status.
5. [docs/UPSTREAM.md](docs/UPSTREAM.md) — the vendored-fork sync model.
6. The `AGENTS.md` of the component you are about to touch.

## Start of a session

```sh
git status
git submodule status
tools/check-dev-env.sh --quick
```

Then read the top of the backlog, pick one item, and say what you are doing and
which files you expect to write. Verify every fact you rely on: a stale document
is a bug, not context.

Rules:

- One backlog item per session unless it is a small follow-up in the same
  component.
- Update the backlog status in the same commit as the work.
- Do not start unrelated work in the same commit. Small doc fixes that the
  current change makes wrong belong in that change.
- If you cannot verify a claim, write that you could not verify it. Never turn
  an assumption into a status row.

## Working with submodules

The submodules are pinned to the gitlinks recorded in the umbrella. A clean
clone checks out detached commits; that is expected.

```sh
git clone --recurse-submodules https://github.com/linuxgamer/uke-fedora.git
git submodule update --init --recursive   # after pulling a gitlink change
```

Flow for a component change:

1. Work and commit on a named branch in the component repository.
2. Push it and open the pull request in that component repository.
3. Run the component checks there and, for anything device-facing, the matching
   image smoke test ([docs/RELEASE.md](docs/RELEASE.md)).
4. Only after the component change is accepted, the umbrella updates the
   gitlink in a separate pull request. Do not bundle component commits into the
   umbrella.

Never move a gitlink "to pick up a fix" without saying which component commit it
points to and what was tested. Never rewrite a published tag or release asset.

## Task loop and definition of done

1. Pick the top unblocked item from `docs/BACKLOG.md`, or record a new item
   before starting.
2. Confirm scope and write down the files you own. Re-read a file before editing
   it; if it changed meanwhile, rebase your edit on the current content.
3. Implement the smallest change that satisfies the item.
4. Run the checks that cover the change, not only a syntax check (see below).
5. Update `docs/STATE.md` and the backlog status.
6. Commit in English, push, and fix CI if the change broke it.

Done means: the relevant checks passed (or their absence is stated), evidence is
recorded, docs are updated, no secret or OEM blob is committed, and any submodule
pointer move is intentional and explained.

## Checks

Full setup, expected outputs and known failure modes are in
[docs/DEVELOPING.md](docs/DEVELOPING.md#checks). The short version:

| Command | Covers | Notes |
| --- | --- | --- |
| `tools/check-dev-env.sh` | Clone shape, submodules, host tools | Use `--quick` for docs-only work |
| `tools/check-docs.sh` | Relative links in published docs | Run for every documentation change |
| `make -C senemos-uke-kernel check-pins` | Source and manifest digests | Fast |
| `make -C senemos-uke-kernel validate` | Kernel source contracts | Needs `rpm`, `rpmspec`, `dtc`, `clang`; can fail silently, see DEVELOPING |
| `make -C uke-linux-hardware-support validate` | Package, source and schema contracts | Fast enough for every change |
| `bash -n` on builder scripts | Syntax only | Fast gate, not CI parity |
| `tools/sync-upstream.sh status` / `verify` | Pin, drift, sync policy | Read-only; `verify` needs a clean tree |

CI: kernel `source-contracts` (pull request), builder `source-contracts`
(push and pull request), umbrella `build-image` (manual). The builder CI also
runs `shellcheck` and the full contract suite; there is no local one-shot runner
yet, so reproduce the commands from
[uke-fedora-builder source-contracts](https://github.com/linuxgamer/uke-fedora-builder/blob/main/.github/workflows/source-contracts.yml).

## Building

Two entry points exist and they are not interchangeable:

- **Images** — `./uke-fedora-builder/build-images.sh` (or `./ukelinux.sh`),
  from the umbrella. Needs Docker or Podman, `avbtool`, `jq`, `g++`, `zstd`,
  about 25 GiB free, and a long first run. Requirements, cache and resume logic:
  [build guide](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILDING.md)
  and [cache guide](https://github.com/linuxgamer/uke-fedora-builder/blob/main/docs/BUILD-CACHE.md).
- **Kernel only** — `senemos.sh` inside the kernel repository, for kernel
  development and verification without an image. It can install host packages
  and needs the same order of free space.

Builds write only under `build/` (gitignored). Do not run two builds into the
same output directory, do not kill another agent's build, and use
`--status`/`--stop` to manage your own. The builder never flashes a device.

## Documentation rules

- Developer docs are [docs/](docs/) and this file; user docs are
  [README.md](README.md) and [docs/INSTALL.md](docs/INSTALL.md). Keep the audiences
  separate: commands, evidence and limitations go to developer docs.
- Write English. State the date, environment, observed result and remaining
  work. Name the device directly.
- Remove a superseded engineering document in the same change that makes
  it obsolete. The 2026-11-11 cleanup removed documents created before
  November 2026 that were not README/AGENTS/BUILDING/SECURITY, not
  maintained in November, and not referenced by code, manifests or a kept
  document; recover them from git history. Component documents stay in the
  component repository.
- Link only to files that exist in the published tree. **Never use a relative
  link into a submodule**: GitHub returns 404 for it. Use the component
  repository URL instead. `tools/check-docs.sh` enforces this.
- Do not link to `private/`, `build/` or `artifacts/`; they are not published.
- Keep [docs/STATE.md](docs/STATE.md) and [docs/BACKLOG.md](docs/BACKLOG.md)
  current. Record facts, not a diary; long history belongs in the private notes.
- Keep user-facing claims consistent with the hardware table and the actual
  release. A successful build is not a boot test.

Document map:

| File | Audience | Purpose |
| --- | --- | --- |
| `README.md` | users | Project, hardware status, downloads |
| `docs/INSTALL.md` | users | Flashing and recovery |
| `docs/DEVELOPING.md` | contributors | First-hour setup, checks, git flow |
| `docs/STATE.md` | contributors | Current heads, CI, blockers |
| `docs/BACKLOG.md` | contributors | Ordered work |
| `docs/UPSTREAM.md` | maintainers | Vendored-fork sync model |
| `docs/RELEASE.md` | maintainers | Build, package, publish, smoke test |
| `docs/COPR.md` | maintainers | Package publishing |
| `docs/FEDORA-BUMP.md` | maintainers | Fedora release bump |
| `docs/HARDWARE.md` | contributors | Evidence per hardware block |
| `docs/CONTRIBUTING.md` | everyone | Bug reports, code contributions, policy |
| `AGENTS.md` | contributors, AI agents | Rules for changing the repository |

## Rules for AI agents

- Verify first. Cite the file and line or the command output for every factual
  claim. Do not invent paths, flags, test results or hardware behaviour.
- If an instruction points to a path that does not exist in the clone, treat it
  as a documentation bug: say so, use the substitutes listed in
  [docs/DEVELOPING.md](docs/DEVELOPING.md#missing-evidence-paths), and fix the
  instruction where it lives. Never fabricate donor evidence or measurements.
- Declare your write scope. Do not edit files another agent is editing. Two
  concurrent agents may write only disjoint sets of files or disjoint
  components. Re-read before every edit; on a conflict, rebase the edit onto the
  current file instead of overwriting it.
- Subagents: use them for independent read-only research or for a disjoint set
  of files, at most two at a time. Give absolute paths, the expected output and
  an explicit "do not edit" unless a write scope is named. The main agent
  reviews every diff and runs the checks; the main agent commits.
- Do not use subagents to avoid reading the code yourself, and do not let a
  subagent move gitlinks, push branches or touch the device.
- Never flash, repartition, switch slots or re-lock the bootloader without an
  explicit user request. Never publish OEM firmware or calibration data.
- Never commit or paste credentials, tokens, private logs, serial numbers,
  home-directory paths or personal data. If a secret was exposed, say so
  privately and rotate it; do not repeat the value.
- Do not rewrite shared history, force-push shared branches, reset another
  agent's work, or delete build caches that an active build is using.

## Safety

- The tablet is a development device with an unlocked bootloader and no
  guaranteed recovery. Preserve `boot_a`, the stock bootloader contract and a
  working recovery route. `userdata` installs erase Android data.
- Keep source, build, package, VM and on-device results separate. A build or a
  checksum does not prove boot, and a boot does not prove a hardware block.
- OEM firmware, sensor blobs and calibration stay out of public repositories;
  see [docs/COPR.md](docs/COPR.md).
- Security reports: do not open a public issue with exploit details. Use
  GitHub's private vulnerability reporting on this repository when available;
  otherwise open a minimal issue asking for a private channel.

## End-of-session checklist

- [ ] `docs/STATE.md` states the new facts (submodule heads, CI, COPR, blockers);
      the umbrella head is "this handoff commit", no self-referencing hash.
- [ ] `docs/BACKLOG.md` marks what moved, what is blocked, and what is new.
- [ ] The relevant checks were run; exceptions are written down.
- [ ] `tools/check-docs.sh` passes for documentation changes.
- [ ] Commits are pushed; submodule pointer changes are intentional.
- [ ] The next action is one line and does not depend on this conversation.
