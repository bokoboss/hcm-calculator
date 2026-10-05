"""Thailand/LHT functional-role adapter over the qualified Chapter 18 engine."""

from __future__ import annotations

from typing import Any, Mapping

from hcmcalc.application.urban_street_workflow import (
    DISPLAY_FIELDS,
    UrbanStreetWorkflow,
    _example_inputs,
    _field_schema as _rht_field_schema,
)
METHOD_ID = "urban_street_segment_th_lht"
TEMPLATE_ID = "USS-TH-LHT-CH30-EP1"
SIDE_FIELD_RENAMES = {
    "curb_proportion": "kerbside_curb_proportion",
    "parking_proportion": "kerbside_parking_proportion",
    "subject_side_access_count": "subject_kerbside_access_count",
    "opposing_side_access_count": "opposing_kerbside_access_count",
}
DISPLAY_FIELDS = tuple(SIDE_FIELD_RENAMES.get(field, field) for field in DISPLAY_FIELDS) + (
    "calibration_status",
    "calibration_source_note",
)


class ThailandLHTUrbanStreetWorkflow(UrbanStreetWorkflow):
    """LHT display semantics with shared Chapter 18 normalization and validation."""

    method_id = METHOD_ID
    template_id = TEMPLATE_ID
    display_fields = DISPLAY_FIELDS
    side_field_names = {
        canonical: display for canonical, display in SIDE_FIELD_RENAMES.items()
    }
    template_label = "HCM Chapter 30 Example Problem 1 — Thailand/LHT semantic mirror"
    template_description = (
        "HCM Chapter 30 Example Problem 1 represented through Thailand/LHT "
        "functional kerbside semantics for adapter verification; not a published Thai example."
    )
    blank_label = "Blank custom analysis"
    blank_description = "Supply every bounded engineering input and external qualification explicitly."
    scope_notes = (
        "Bounded HCM 7.0 Chapter 18 signalized 15-minute segment; external downstream through performance is required.",
        "Thailand/LHT functional-role semantic adapter: kerbside is physical left for each travel direction.",
        "HCM-reference coefficients; not locally calibrated by default. Turn-side and planning procedures remain unavailable.",
    )
    workflow_scope = "bounded_hcm7_signalized_15min_th_lht_hcm_reference"

    def _field_schema(self) -> list[dict[str, Any]]:
        fields = _rht_field_schema()
        for field in fields:
            old = field["key"]
            key = SIDE_FIELD_RENAMES.get(old, old)
            field["key"] = key
            field["label_key"] = f"{METHOD_ID}.{key}"
        fields.extend([
            {
                "key": "calibration_status",
                "label_key": f"{METHOD_ID}.calibration_status",
                "kind": "choice",
                "required": True,
                "options": ["hcm_reference_uncalibrated", "user_local_calibration"],
            },
            {
                "key": "calibration_source_note",
                "label_key": f"{METHOD_ID}.calibration_source_note",
                "kind": "text",
                "required": False,
            },
        ])
        return fields

    def extra_segment_fields(self) -> tuple[str, ...]:
        return ("calibration_status", "calibration_source_note")

    def external_group_fields(self) -> tuple[str, ...]:
        return tuple(
            field for field in self.display_fields[22:]
            if field not in self.extra_segment_fields()
        )

    def _example_values(self, unit: str) -> dict[str, Any]:
        rht_values = _example_inputs(unit)
        values = {
            SIDE_FIELD_RENAMES.get(key, key): value
            for key, value in rht_values.items()
        }
        values.update({
            "calibration_status": "hcm_reference_uncalibrated",
            "calibration_source_note": None,
        })
        return values

    def _validate_application_fields(
        self, values: Mapping[str, Any], normalized: Mapping[str, Any]
    ) -> None:
        from hcmcalc.application.workflows import ApplicationWorkflowError

        status = values.get("calibration_status")
        note = values.get("calibration_source_note")
        if status not in {"hcm_reference_uncalibrated", "user_local_calibration"}:
            raise ApplicationWorkflowError(
                "Choose a supported calibration status.",
                code="invalid_input",
                message_key="api.invalid_input",
                details={"field": "calibration_status"},
            )
        if note is not None and not isinstance(note, str):
            raise ApplicationWorkflowError(
                "Calibration source note must be text or null.",
                code="invalid_input",
                message_key="api.invalid_input",
                details={"field": "calibration_source_note"},
            )
        if status == "hcm_reference_uncalibrated" and normalized["s_calib_mph"] != 0:
            raise ApplicationWorkflowError(
                "HCM reference uncalibrated requires s_calib = 0.",
                code="invalid_input",
                message_key="api.invalid_input",
                details={"field": "s_calib"},
            )
        if status == "user_local_calibration" and (
            not isinstance(note, str) or not note.strip()
        ):
            raise ApplicationWorkflowError(
                "User local calibration requires a nonempty calibration source note.",
                code="invalid_input",
                message_key="api.invalid_input",
                details={"field": "calibration_source_note"},
            )

    def _audit_metadata_for(self, displayed_inputs: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "traffic_side": "left_hand_traffic",
            "kerbside_physical_side": "left_for_each_travel_direction",
            "input_contract": "hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1",
            "calibration_status": displayed_inputs.get("calibration_status"),
            "calibration_source_note": displayed_inputs.get("calibration_source_note"),
            "semantic_field_mappings": {
                public: canonical
                for canonical, public in SIDE_FIELD_RENAMES.items()
            },
        }
