from importlib.resources import files

from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.weaving_diagrams import get_weaving_diagram
from hcmcalc.ui.manual_ramp_influence import diagram_path


def test_required_ui_assets_resolve_from_package_resources() -> None:
    package_root = files("hcmcalc.ui")

    expected_assets = (
        package_root.joinpath("data", "example_inputs.yaml"),
        package_root.joinpath("data", "multilane_example_inputs.yaml"),
        package_root.joinpath("data", "freeway_example_inputs.yaml"),
        package_root.joinpath("data", "weaving_example_inputs.yaml"),
        package_root.joinpath("data", "merge_diverge_example_inputs.yaml"),
        package_root.joinpath("assets", "two_lane", "passing_constrained.png"),
        package_root.joinpath("assets", "two_lane", "passing_zone.png"),
        package_root.joinpath("assets", "two_lane", "passing_lane.png"),
        package_root.joinpath("assets", "weaving", "one_sided_weave.png"),
        package_root.joinpath("assets", "weaving", "two_sided_weave.png"),
        package_root.joinpath("assets", "ramp_influence", "merge_right_on_ramp.svg"),
        package_root.joinpath("assets", "ramp_influence", "diverge_right_off_ramp.svg"),
    )

    for asset in expected_assets:
        assert asset.is_file(), f"Missing packaged UI asset: {asset}"


def test_public_asset_resolvers_return_existing_packaged_paths() -> None:
    for segment_type in ("passing_constrained", "passing_zone", "passing_lane"):
        schematic = get_segment_schematic_path(segment_type)
        assert schematic is not None
        assert schematic.is_file()
        assert "hcmcalc" in schematic.parts

    one_sided = get_weaving_diagram("one_sided_major")
    two_sided = get_weaving_diagram("two_sided")
    assert one_sided is not None and one_sided.path.is_file()
    assert two_sided is not None and two_sided.path.is_file()

    assert diagram_path("merge").is_file()
    assert diagram_path("diverge").is_file()
