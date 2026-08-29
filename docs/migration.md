# Migration from Humanizer Russian

Date: 2026-08-29.

Origin: `Antiokh/humanizer_russian` PR #80, `feat/legal-document-layer`.

## What moved

Substantive legal/document work was repackaged into this repository:

- public normative/methodological source inventory;
- public-source atomic rules and evals;
- specialist book corpus inventory, coverage, audit, rules and evals;
- compact legal-document reference;
- document profiles;
- source/status policy;
- conflict resolver semantics.

## What did not move verbatim

The old PR contained many small design-note files tied to Humanizer's internal checker architecture. They were consolidated rather than copied one-for-one.

Humanizer-specific compatibility notes such as its existing Markdown parser, generic anti-calque rules and internal finding schema remain Humanizer concerns. Legalizer instead exposes explicit `protect`, `disable`, `downgrade` and `override` semantics so an integration can resolve conflicts without importing Humanizer's policy.

## Migration principle

No substantive source-derived rule was intentionally discarded. Redundant planning notes were normalized into:

- `docs/architecture.md`
- `core/rule-schema.yaml`
- `profiles/profiles.yaml`
- `rules/rules.yaml`
- `references/legal-russian.md`
- `studies/public-sources/`
- `studies/book-corpus/`

## Upstream relationship

Legalizer Russian is now the source of truth for legal/official-document rules. Humanizer Russian may later consume Legalizer as an optional professional profile/integration, but should not duplicate the legal rules internally.
