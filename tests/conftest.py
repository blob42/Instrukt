import pytest

def pytest_addoption(parser):
    parser.addoption(
            "--fast-index", action="store_true", help="skip slow operations on index tests"
            )

@pytest.fixture
def fastindex(request):
    """skip slow operations on index tests"""
    return request.config.getoption("--fast-index")
