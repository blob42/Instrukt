import os
import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile
from unittest import mock
from instrukt.config import ConfigManager

@pytest.fixture
def ctx():
    return mock.Mock()

class TestConfigManager:

    @pytest.mark.skipif(os.name == 'nt', reason="requires unix")
    def test_init(self, monkeypatch, ctx):
        cm = ConfigManager(ctx, config_file="test.yml")
        assert cm.config_path == str(Path("~/.config/instrukt/test.yml").expanduser())
