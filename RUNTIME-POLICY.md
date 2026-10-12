# Runtime and desktop policy

Owner decision, 2026-10-11: the blanket Python prohibition is withdrawn.

Use unmodified Fedora packages, libraries and applications with their normal
dependencies, including Python. Pin full package closures; audit signatures,
provenance, architecture, privacy and reproducibility. Language alone is not
a release rejection criterion. Do not fork GNU/GLib or app stacks to remove it.

Hardware support is DE-neutral. The builder owns base/DE selection; themes and
DE-specific UI are optional. GNOME, Plasma and Xfce selector sources are not yet
dependency-resolved/qualified images.

Boot/recovery are bounded deployment environments. Current minimal recovery has
no qualified Python interpreter; its profile-specific audit is not a global ban.
Any new interpreter there needs dependency/size/runtime qualification. Kernel
and UEFI retain their supported native implementation models.

Historical reports, locks and schema-1 manifests keep their original meaning.
Schema-2 boot manifests carry payload-validation/Fedora-runtime policy evidence.
Old core vendor-swap transactions are blocked pending replacement/qualification.
No hardware result is inferred from these changes.
