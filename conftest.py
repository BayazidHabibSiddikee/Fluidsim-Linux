"""Pytest fixtures: one QApplication shared across the whole test session.

Several test modules create QApplication instances at import time, which
crashes with "Please destroy the QApplication singleton" when pytest
collects them all into a single process. This fixture guarantees exactly
one application for the session and makes the offscreen platform the
default so tests run headless.
"""
import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    yield app