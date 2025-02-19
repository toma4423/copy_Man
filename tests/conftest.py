import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-gui", action="store_true", default=False, help="Skip GUI tests"
    )


@pytest.fixture
def skip_gui(request):
    return request.config.getoption("--skip-gui")
