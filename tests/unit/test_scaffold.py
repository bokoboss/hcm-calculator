from hcmcalc import __version__
from hcmcalc.methods import available_methods


def test_package_imports() -> None:
    assert __version__ == "0.5.0"


def test_method_registry_includes_implemented_example_targets() -> None:
    methods = {method.key: method for method in available_methods()}

    assert methods["hcm7_ch15_two_lane_motorized"].status == "implemented_example_only"
    assert (
        methods["hcm7_multilane_los"].status
        == "bounded_multilane_segment_v0_1"
    )
