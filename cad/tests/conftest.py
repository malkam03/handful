"""pytest setup: build the parts on every core before the test workers start."""

from tests import partcache


def pytest_configure(config):
    if not hasattr(config, "workerinput"):  # the controller, not an xdist worker
        partcache.prebuild()
