# v0.4.1 — Cross-method consolidation and post-release hardening

## Consolidation summary

v0.4.1 consolidates the qualified Two-Lane Highway Segment, Two-Lane Highway
Facility, Multilane Highway Segment, and Basic Freeway Segment product
contracts. It introduces no HCM equation, lookup table, vehicle class, or
facility type.

## Terminology and shared UX

The [supported methods matrix](../methodology/supported_methods_matrix.md)
defines the canonical labels and intentional distinctions. In particular,
follower density remains a Two-Lane measure; Multilane and Basic Freeway density
remain `pc/mi/ln` or `pc/km/ln`; and base/adjusted FFS, capacity, and operating
speed are not conflated.

Every visible calculator remains a compact single-page worksheet with the
same high-level progression: setup; roadway/geometry; traffic; heavy vehicles;
applicable advanced adjustments; calculate; results; audit; and save/export.
Inactive measured/estimated FFS and PCE-mode controls normalize to
non-operative values, so hidden state cannot alter a calculation identity.

## Persistence hardening

Project schema remains **1.2**: the stored file shape did not change
materially. Calculation fingerprints now consistently include the method
identifier, the input-contract version, and effective normalized inputs.
Projects using an older supported schema are reported as migrated. A stored
result that cannot be verified under the current contract is discarded with a
clear recalculation message; stale results remain ineligible for export.

## Export and report contract

JSON, CSV, Excel, Markdown, and report JSON are renderings of an existing
engine result and do not recalculate methodology. They preserve selected display
units, normalized engine-input audit context, assumptions, warnings,
limitations, provenance, and null semantics. Values not predicted above
capacity remain null/blank/**Not predicted**, never zero.

## Accessibility and interaction fixes

- UI-boundary numeric values consistently reject boolean, NaN, and infinite
  values before normalization.
- Multilane and Basic Freeway adapters reject unknown UI fields instead of
  permitting cross-method state to leak into an engine payload.
- Project loading explicitly distinguishes a current result, a migrated
  project, and a project requiring recalculation.

## Regression evidence

- Protected baseline before consolidation: **860 passed** on Python 3.12.10.
- Existing Chapter 26 Two-Lane examples, facility examples, Multilane Example
  4, and Basic Freeway Example 1 remain the protected numerical fixtures.
- Targeted integration tests cover normalization, method/contract fingerprints,
  persistence status, stale-result gating, reporting, and Streamlit adapters.

## Documentation updates

- Added the authoritative [supported methods matrix](../methodology/supported_methods_matrix.md).
- Updated the README, quick-start, supported-workflows guide, and roadmap.
- This release note is the v0.4.1 cross-method consolidation record.

## No-methodology-change statement and retained limitations

**No qualified engineering result changed.** This release deliberately does
not add ramps, merge/diverge, weaving, freeway facilities, corridor analysis,
reliability analysis, oversaturated prediction, or new/unsupported PCE domains.
Those candidates require their own reference audit, engine phase, and
integration/release phase.

