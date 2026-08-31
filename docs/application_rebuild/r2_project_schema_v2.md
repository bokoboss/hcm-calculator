# Project v2 persistence contract

Status: Phase 2 prototype authority

Project v2 is a portable JSON document for the application rebuild. It is
storage-agnostic: the browser can download/open the document and the local API
can validate or transform it, but no database or recent-project service is
introduced.

## Graph and identity

The durable graph is:

```text
Project
└── Analysis (method and contract identity)
    └── Scenario (independent displayed/normalized inputs)
        └── Result (retained engine result, only when current)
```

Every Project, Analysis, Scenario, and retained Result has a stable generated
identifier. The nested relationship is authoritative; scenario IDs are unique
within an analysis and result IDs are unique for each retained result.

An Analysis stores the backend-authoritative method identity:

- `method_id`
- `method_identifier`
- `engine_method_identifier`
- `method_version`
- `input_contract`
- `project_type`
- HCM edition/chapter metadata

A Scenario stores both `displayed_inputs` and `normalized_inputs`, its unit and
starting template, and two fingerprints:

- `calculation_fingerprint` preserves the existing method/contract/normalized
  input fingerprint contract;
- `input_snapshot_fingerprint` also covers the displayed worksheet snapshot so
  the application can recognize an exact current/stale document state.

## Result retention and presentation boundary

A Scenario result is retained only when its method identity, input contract,
method version, calculation fingerprint, and input snapshot fingerprint all
match the scenario. Result records retain the engine result, warnings,
assumptions, and audit evidence. They do not retain a serialized `presentation`
object or rendered report. Presentation is derived after load from the current
result and the selected locale/unit system.

Changing scenario inputs discards the retained result and marks the scenario
`stale`; duplicating a scenario creates an independent `not_calculated`
scenario. Compare accepts only two `current` results in the same Analysis and
never executes an HCM engine.

## Versioning and legacy import

The current document has `schema_version: "2.0"`. Unknown/future `2.x` versions
are rejected rather than guessed. Legacy `1.0`, `1.1`, and `1.2` manual
documents are imported into the graph with a migration record. Legacy result
payloads are retained only when their stored fingerprint and engine method
identity match the recomputed normalized identity; mismatched or missing
results are discarded without a silent calculation rerun.

All seven delivered workflows use the same graph and persistence contract:

- `two_lane_segment` → `hcm7_two_lane_highway_segment` /
  `phase_5_product_integration`;
- `multilane_segment` → `hcm7_multilane_los` / `phase_8`;
- `two_lane_facility` → `hcm7_two_lane_highway_facility` /
  `phase_5_product_integration`.
- `basic_freeway_segment` → `hcm7_basic_freeway_segment` /
  `phase_10_product_integration`;
- `weaving_segment` → `weaving_segment` /
  `hcm_7_0_weaving_segment_operational_v1`;
- `merge_segment` and `diverge_segment` retain their exact Chapter 14
  operational contracts.
