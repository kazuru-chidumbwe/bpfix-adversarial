# SPDX-License-Identifier: MIT
"""Third-party reporter adapters. One entry per adapter; see docs/ADDING-A-REPORTER.md."""

from __future__ import annotations

from .prevail import Prevail
from .pretty_verifier import PrettyVerifier

ADAPTERS: tuple = (PrettyVerifier, Prevail)
