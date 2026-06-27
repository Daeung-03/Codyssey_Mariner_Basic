import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from budget_app import cli


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.data_dir = Path(self._tmpdir.name) / "data"
        self.log_dir = Path(self._tmpdir.name) / "logs"

    def run_cli(self, *args, data_dir=None):
        argv = ["--data-dir", str(data_dir or self.data_dir), *args]
        buf = StringIO()
        with redirect_stdout(buf):
            code = cli.main(argv, log_dir=self.log_dir)
        return code, buf.getvalue()

    def add_transaction(self, date, type_, category, amount, memo="", tags=""):
        answers = iter([date, type_, category, str(amount), memo, tags])
        with patch("builtins.input", lambda _prompt="": next(answers)):
            return self.run_cli("add")
