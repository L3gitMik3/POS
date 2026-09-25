"""Backward-compatible shim for the project settings.

The actual configuration lives in config/settings/*.py.
"""

from config.settings.dev import *  # noqa: F401,F403
