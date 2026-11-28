# Working on Uke Linux

- Read `README.md` for the layout. Keep new folders inside the existing top-level folders.
- Put component docs under `docs/<component>/`, using the matching project folder name. Keep project-wide docs directly under `docs/`.
- If available, read `private/TODO.md` and `private/HANDOFF.md` before starting. Use `TODO.md` for pending work and update `HANDOFF.md` when leaving work another agent needs to continue. Keep handoffs short and concrete.
- Put build orchestration in Python under `build/`. Use existing tools for compilation, packaging, and image creation. Keep build scratch space under `build/work/`.
- Keep Senemos-specific pins, patches, and integration in `kernel/`. Record the upstream revision for any imported code so it can be updated deliberately.
- Keep root filesystem source files in `rootfs/`. Put generated root filesystem trees under `build/work/`.
- Keep unpublished material in `private/` and local build inputs in `build/inputs/local/`. Public documentation should work from a clean checkout.
- Use Uke Debug's JSON commands for tablet diagnostics over SSH or TWRP. See `docs/extra/README.md` for examples. The maintainer runs all fastboot commands.
