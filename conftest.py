"""Put this leg's ``src/`` layout on ``sys.path`` for pytest.

Created by the OQ-O scaffold-levelling pass (openxFactory#656) before any
carved content arrives; ``pyproject.toml`` records why the import root has to
exist at all. That file's ``[tool.pytest.ini_options] pythonpath = ["src"]``
does this same job whenever pytest reads that table; this module is the belt
to that pair of braces — it also runs under a runner invoked against a
different ini, and it is the root of the conftest chain that the suites
arriving under ``tests/`` are collected beneath.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"

if SRC.is_dir():
    _src = str(SRC)
    if _src not in sys.path:
        sys.path.insert(0, _src)


# ---------------------------------------------------------------------------
# THE HOST'S REGISTRATION, MADE AT TEST-PROCESS START (§ 4.4, RULING C2).
#
# `openxdox` is the domain-mapping CORE and ships NO domain's words: since
# § 4.4 the lifecycle engine reads its status vocabulary, terminal statuses and
# immutability point from a profile a DESCENDANT registers at process start
# (RULED ASK-4 Q1/Q5, openxFactory#656 comment 5634195861). A suite that drives
# the engine is a host like any other, so it makes the host's call here, in the
# root of the conftest chain — which IS process start for a pytest run. That is
# not a test convenience standing in for the contract; it is the contract,
# exercised.
#
# The profile is the VENDORED FIXTURE — openXdox-spec's worked example of
# openxFactory's own engineering profile, carrying the corrected nine-word
# taxonomy. The REAL instance is authored at `opensoft/openxFactory` and
# registered by ITS adapter; nothing under `src/` loads this file.
#
# It is registered UNCONDITIONALLY and never behind a try/except: a suite that
# silently ran with no profile would be a suite in which the refusal this slice
# exists to install looks like a passing test.
from openxdox import domain_profile as _domain_profile  # noqa: E402

DOMAIN_PROFILE_FIXTURE = (
    Path(__file__).resolve().parent / "tests" / "fixtures"
    / "openxfactory-engineering-profile.yaml")

_domain_profile.register(_domain_profile.load(DOMAIN_PROFILE_FIXTURE))
