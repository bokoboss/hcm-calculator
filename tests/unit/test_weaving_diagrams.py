from __future__ import annotations

from pathlib import Path

import pytest

from hcmcalc.ui.manual_weaving import (
    WEAVING_CALCULATION_CONTRACT,
    WEAVING_METHOD_IDENTIFIER,
    weaving_preset_ui_inputs,
    weaving_ui_inputs_to_engine,
)
from hcmcalc.ui.weaving_diagrams import get_weaving_diagram, get_weaving_diagram_subtype
from hcmcalc.ui.workflow_state import calculation_input_fingerprint


@pytest.mark.parametrize(
    ("configuration", "number_of_weaving_lanes", "expected"),
    [
        ("one_sided", 3, "one_sided_major"),
        ("one_sided", 2, "one_sided_ramp"),
        ("two_sided", 0, "two_sided"),
        ("two_sided", 2, None),
        ("one_sided", 0, None),
        (None, None, None),
    ],
)
def test_diagram_subtype_is_derived_only_from_coded_configuration(
    configuration: str | None,
    number_of_weaving_lanes: int | None,
    expected: str | None,
) -> None:
    assert get_weaving_diagram_subtype(configuration, number_of_weaving_lanes) == expected


@pytest.mark.parametrize(
    ("preset_id", "expected_subtype", "expected_filename"),
    [
        ("WVG-CH27-001", "one_sided_major", "one_sided_weave.png"),
        ("WVG-CH27-002", "one_sided_ramp", "one_sided_weave.png"),
        ("WVG-CH27-003", "two_sided", "two_sided_weave.png"),
    ],
)
def test_validation_presets_resolve_to_packaged_reference_images(
    preset_id: str,
    expected_subtype: str,
    expected_filename: str,
) -> None:
    ui_inputs = weaving_preset_ui_inputs(preset_id, "imperial")

    subtype = get_weaving_diagram_subtype(
        ui_inputs["configuration"],
        ui_inputs["number_of_weaving_lanes"],
    )
    diagram = get_weaving_diagram(subtype)

    assert subtype == expected_subtype
    assert diagram is not None
    assert diagram.filename == expected_filename
    assert diagram.path.is_file()
    assert diagram.path.name == expected_filename


def test_diagram_subtype_is_not_a_calculation_input_or_fingerprint_field() -> None:
    displayed = weaving_preset_ui_inputs("WVG-CH27-001", "imperial")
    normalized = weaving_ui_inputs_to_engine(displayed, "imperial")
    baseline = calculation_input_fingerprint(
        WEAVING_METHOD_IDENTIFIER,
        WEAVING_CALCULATION_CONTRACT,
        normalized,
    )

    subtype = get_weaving_diagram_subtype(
        displayed["configuration"],
        displayed["number_of_weaving_lanes"],
    )

    assert subtype == "one_sided_major"
    assert "diagram_subtype" not in normalized
    assert "weaving_diagram_subtype" not in normalized
    assert calculation_input_fingerprint(
        WEAVING_METHOD_IDENTIFIER,
        WEAVING_CALCULATION_CONTRACT,
        normalized,
    ) == baseline


def test_diagram_helper_has_no_legacy_runtime_dependency() -> None:
    source = Path("src/hcmcalc/ui/weaving_diagrams.py").read_text(encoding="utf-8")

    assert "hcm7-weaving-segments" not in source
    assert "raw.githubusercontent.com" not in source


def test_streamlit_weaving_reference_image_renders_on_public_page() -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(Path(__file__).parents[2] / "src" / "hcmcalc" / "ui" / "streamlit_app.py")
    )
    app.run(timeout=30)
    app.selectbox[1].set_value("freeways").run(timeout=30)
    app.selectbox[2].set_value("manual_weaving").run(timeout=30)

    markdown_values = [item.value for item in app.markdown]
    caption_values = [item.value for item in app.caption]

    assert not app.exception
    assert any("One-sided major weave" in value for value in markdown_values)
    assert any("configuration coding aid" in value for value in caption_values)
    assert len(app.image) == 1
