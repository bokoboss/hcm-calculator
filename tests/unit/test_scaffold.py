from hcmcalc import __version__
from hcmcalc.methods import available_methods


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_method_registry_includes_initial_and_future_targets() -> None:
    methods = {method.key: method for method in available_methods()}

    assert methods["hcm7_ch15_two_lane_motorized"].status == "planned"
    assert methods["hcm7_multilane_los"].status == "future"
