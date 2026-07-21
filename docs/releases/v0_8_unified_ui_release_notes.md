# v0.8 Unified UI Release Notes

Status: locally release-qualified by Phase 15.3.

Version 0.8 qualifies the unified app-wide UI introduced through Phase 15.2.

Highlights:

- Grouped navigation for Roadways, Freeways, and Reference.
- Eight visible modes: Two-Lane Segment, Two-Lane Facility, Multilane Segment,
  Basic Freeway Segment, Weaving Segment, Merge Segment, Diverge Segment, and
  Supported Workflows.
- Shared English and Thai presentation across calculator navigation, worksheet
  sections, result states, project messages, and export surfaces.
- Unified result-state handling for prerun, stable, warning, capacity failure,
  stale, invalid, unsupported, handoff, and internal-error paths.
- Stale-result protection that hides old metrics and blocks report exports
  until recalculation.
- Multilane browser input edits now participate in stale-result protection
  immediately instead of being buffered inside a Streamlit form.
- Packaged runtime assets and preset data so the installed wheel can launch
  calculator routes without a source checkout.
- Preserved numerical contracts, project schemas, fingerprints, and export
  field names.

Release artifact:

- Wheel: `hcm_calculator-0.8.0-py3-none-any.whl`
- SHA-256:
  `4bf6a3bc2f60c890070d1e681843ef112864cd2b3fa3a542e3b5f6d274549989`

Known limitations:

- The calculator remains limited to the documented HCM 7.0/7th Edition bounded
  workflows.
- HCM 7.1, new geometry support, standalone executable packaging, and installer
  workflows are outside this release.
- PDF and DOCX report exports are not implemented.
