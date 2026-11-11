# Pull request

## Summary

What changed and why. Name the component and the commit(s) when a submodule
pointer is involved.

## Checks

List the exact commands and their results. Check what applies; say explicitly
what was not run and why.

- [ ] `tools/check-dev-env.sh` (or `--quick` for documentation-only changes)
- [ ] `tools/check-docs.sh` (documentation changes)
- [ ] `make -C senemos-uke-kernel check-pins`
- [ ] `make -C senemos-uke-kernel validate`
- [ ] `make -C uke-linux-hardware-support validate`
- [ ] Builder: `bash -n` and, for script changes, the commands from
      `uke-fedora-builder/.github/workflows/source-contracts.yml`
- [ ] `tools/sync-upstream.sh verify` (pin or sync changes)
- [ ] Device smoke test — not applicable / describe

## Limitations

What was not tested, which host was used, and any result that remains unverified.

## Device and submodule pointer

- [ ] No device action.
- [ ] No gitlink change in this pull request.
- [ ] Gitlink change: component repository, commit, and what was tested:

## Safety

- [ ] No credentials, private logs, serial numbers, calibration or OEM blobs.
- [ ] No relative links into submodules (they 404 on GitHub).
- [ ] User-facing claims match the hardware table and the tested release.
