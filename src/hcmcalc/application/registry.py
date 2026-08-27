"""Authoritative backend metadata registry for current HCM analyses.

The registry describes engineering support and identity.  It does not select
frontend modules and it does not execute calculations.  That separation keeps
the normal rebuilt UI from treating backend availability as frontend delivery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AnalysisDefinition:
    """Stable engineering metadata for one analysis method.

    ``method_identifier`` and ``input_contract`` are the existing
    application/persistence identities used by project fingerprints.  The
    qualified engine/result identity is recorded separately because several
    legacy adapters intentionally use a method family or workflow identity at
    the persistence boundary.
    """

    method_id: str
    family: str
    name_key: str
    description_key: str
    method_identifier: str
    engine_method_identifier: str
    method_version: str
    input_contract: str
    project_type: str
    hcm_edition: str
    hcm_chapter: str
    chapter_reference: str
    supported_unit_systems: tuple[str, ...]
    availability: str
    capabilities: tuple[str, ...]
    scope_summary_keys: tuple[str, ...]
    legacy_workflow: str | None = None

    @property
    def engineering_available(self) -> bool:
        """Whether the qualified Python/engine boundary supports this entry."""

        return True

    def to_mapping(self) -> dict[str, Any]:
        """Return an API/fixture-friendly mapping with stable field names."""

        return {
            "method_id": self.method_id,
            "family": self.family,
            "name_key": self.name_key,
            "description_key": self.description_key,
            "method_identifier": self.method_identifier,
            "engine_method_identifier": self.engine_method_identifier,
            "method_version": self.method_version,
            "input_contract": self.input_contract,
            "project_type": self.project_type,
            "hcm_edition": self.hcm_edition,
            "hcm_chapter": self.hcm_chapter,
            "chapter_reference": self.chapter_reference,
            "supported_unit_systems": list(self.supported_unit_systems),
            "availability": self.availability,
            "engineering_available": self.engineering_available,
            "capabilities": list(self.capabilities),
            "scope_summary_keys": list(self.scope_summary_keys),
            "legacy_workflow": self.legacy_workflow,
        }


_COMMON_UNITS = ("metric", "imperial")

_ANALYSIS_DEFINITIONS: tuple[AnalysisDefinition, ...] = (
    AnalysisDefinition(
        method_id="two_lane_segment",
        family="highways",
        name_key="method.two_lane_segment.name",
        description_key="method.two_lane_segment.description",
        method_identifier="hcm7_two_lane_highway_segment",
        engine_method_identifier="hcm7_ch15_two_lane_motorized",
        method_version="hcm7.0",
        input_contract="phase_5_product_integration",
        project_type="manual_single_segment",
        hcm_edition="HCM 7.0",
        hcm_chapter="15",
        chapter_reference="HCM 7th Edition Chapter 15",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_bounded",
        capabilities=("single_segment", "audit", "legacy_project"),
        scope_summary_keys=("method.two_lane_segment.scope",),
        legacy_workflow="manual_single_segment",
    ),
    AnalysisDefinition(
        method_id="two_lane_facility",
        family="highways",
        name_key="method.two_lane_facility.name",
        description_key="method.two_lane_facility.description",
        method_identifier="hcm7_two_lane_highway_facility",
        engine_method_identifier="hcm7_ch15_two_lane_motorized",
        method_version="hcm7.0",
        input_contract="phase_5_product_integration",
        project_type="manual_two_lane_facility_v1",
        hcm_edition="HCM 7.0",
        hcm_chapter="15",
        chapter_reference="HCM 7th Edition Chapter 15; Chapter 26 Examples 3–4",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_template_bounded",
        capabilities=("facility_template", "audit", "legacy_project"),
        scope_summary_keys=("method.two_lane_facility.scope",),
        legacy_workflow="manual_facility",
    ),
    AnalysisDefinition(
        method_id="multilane_segment",
        family="highways",
        name_key="method.multilane_segment.name",
        description_key="method.multilane_segment.description",
        method_identifier="hcm7_multilane_los",
        engine_method_identifier="hcm7_multilane_los",
        method_version="v0.1",
        input_contract="phase_8",
        project_type="manual_multilane_v0",
        hcm_edition="HCM 7.0",
        hcm_chapter="12",
        chapter_reference="HCM 7th Edition Chapter 12; Chapter 26 Example 4",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_bounded",
        capabilities=("segment", "audit", "legacy_project", "capacity_failure"),
        scope_summary_keys=("method.multilane_segment.scope",),
        legacy_workflow="manual_multilane",
    ),
    AnalysisDefinition(
        method_id="basic_freeway_segment",
        family="freeways",
        name_key="method.basic_freeway_segment.name",
        description_key="method.basic_freeway_segment.description",
        method_identifier="hcm7_basic_freeway_segment",
        engine_method_identifier="hcm7_basic_freeway_segment",
        method_version="phase_9_engine",
        input_contract="phase_10_product_integration",
        project_type="manual_basic_freeway_v0",
        hcm_edition="HCM 7.0",
        hcm_chapter="12",
        chapter_reference="HCM 7th Edition Chapter 12; Chapter 26 Example 1",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_bounded",
        capabilities=("segment", "audit", "legacy_project", "capacity_failure"),
        scope_summary_keys=("method.basic_freeway_segment.scope",),
        legacy_workflow="manual_basic_freeway",
    ),
    AnalysisDefinition(
        method_id="weaving_segment",
        family="freeways",
        name_key="method.weaving_segment.name",
        description_key="method.weaving_segment.description",
        method_identifier="weaving_segment",
        engine_method_identifier="hcm7_v70_freeway_weaving_segment",
        method_version="hcm_7_0",
        input_contract="hcm_7_0_weaving_segment_operational_v1",
        project_type="manual_freeway_weaving_segment_v1",
        hcm_edition="HCM 7.0",
        hcm_chapter="13",
        chapter_reference="HCM 7.0 Chapter 13; Chapter 27 Examples 1–3",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_isolated",
        capabilities=("segment", "audit", "legacy_project", "capacity_failure", "handoff"),
        scope_summary_keys=("method.weaving_segment.scope",),
        legacy_workflow="manual_weaving",
    ),
    AnalysisDefinition(
        method_id="merge_segment",
        family="freeways",
        name_key="method.merge_segment.name",
        description_key="method.merge_segment.description",
        method_identifier="merge_segment",
        engine_method_identifier="hcm7_v70_freeway_merge_segment",
        method_version="hcm_7_0",
        input_contract="hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational",
        project_type="manual_freeway_merge_segment_v1",
        hcm_edition="HCM 7.0",
        hcm_chapter="14",
        chapter_reference="HCM 7.0 Chapter 14; Chapter 28 merge cases",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_isolated",
        capabilities=("segment", "audit", "legacy_project", "capacity_failure"),
        scope_summary_keys=("method.merge_segment.scope",),
        legacy_workflow="manual_merge",
    ),
    AnalysisDefinition(
        method_id="diverge_segment",
        family="freeways",
        name_key="method.diverge_segment.name",
        description_key="method.diverge_segment.description",
        method_identifier="diverge_segment",
        engine_method_identifier="hcm7_v70_freeway_diverge_segment",
        method_version="hcm_7_0",
        input_contract="hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational",
        project_type="manual_freeway_diverge_segment_v1",
        hcm_edition="HCM 7.0",
        hcm_chapter="14",
        chapter_reference="HCM 7.0 Chapter 14; Chapter 28 diverge cases",
        supported_unit_systems=_COMMON_UNITS,
        availability="qualified_isolated",
        capabilities=("segment", "audit", "legacy_project", "capacity_failure"),
        scope_summary_keys=("method.diverge_segment.scope",),
        legacy_workflow="manual_diverge",
    ),
)


class AnalysisRegistry:
    """Read-only registry with stable ordering and language-neutral lookup."""

    def __init__(self, definitions: Iterable[AnalysisDefinition] = _ANALYSIS_DEFINITIONS):
        materialized = tuple(definitions)
        ids = [definition.method_id for definition in materialized]
        if len(ids) != len(set(ids)):
            raise ValueError("Analysis registry method_id values must be unique.")
        self._definitions = materialized
        self._by_id = {definition.method_id: definition for definition in materialized}

    def list(self) -> tuple[AnalysisDefinition, ...]:
        return self._definitions

    def get(self, method_id: str) -> AnalysisDefinition | None:
        return self._by_id.get(method_id)

    def require(self, method_id: str) -> AnalysisDefinition:
        definition = self.get(method_id)
        if definition is None:
            raise KeyError(f"Unknown analysis method_id: {method_id}")
        return definition


_REGISTRY = AnalysisRegistry()


def get_analysis_registry() -> AnalysisRegistry:
    """Return the process-local backend-authoritative registry."""

    return _REGISTRY


def list_analysis_definitions() -> tuple[AnalysisDefinition, ...]:
    return _REGISTRY.list()


def get_analysis_definition(method_id: str) -> AnalysisDefinition | None:
    return _REGISTRY.get(method_id)
