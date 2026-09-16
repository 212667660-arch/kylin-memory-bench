# Third-Party Notices

This file records third-party material known to be relevant to the current
release candidate. It is not a substitute for a final project license or
legal review.

## Runtime dependency

- **PyYAML**: the project declares `PyYAML>=6.0`. The installed openKylin VM
  version was 6.0.1 and the development environment version was 6.0.3; both
  expose MIT license metadata. A target system package must retain the
  corresponding Debian copyright and license files.

## Research references not bundled

The repositories listed in `docs/license-audit.md` were inspected as research
references only. Their source code, datasets, prompts, charts, model outputs,
and transitive dependencies are not copied into `kmb/`, `suites/`,
`examples/`, or the Debian payload. The `.tmp-github-research/` directory is
not a release input. Any future reuse requires a file-level license review,
attribution, and a recorded modification notice.

## Cloud model outputs

Grok and DeepSeek responses in `runs/` are execution evidence, not bundled
third-party software. Before public release or demonstration, remove secrets
and sensitive data and confirm the applicable provider terms for storage and
display.

## Pending confirmation

The project-level license, copyright holders, contribution provenance, cloud
API display terms, and any future external dataset or prompt license remain
subject to project-owner/legal confirmation. No pending item is represented as
an active grant by this notice.
