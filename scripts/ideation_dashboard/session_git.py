# Compatibility shim: the retired pre-carve spelling of `session_git`.
#
# The carve moved `ideation_dashboard/session_git.py` verbatim to openDox-code
# as `opendox.session_git`. One protected suite still spells the old path in a
# module-level string, `LOCK_HOLDER` in `tests/test_session_transaction.py`:
# a rival process runs `from ideation_dashboard import session_git as sg`
# after putting this directory's parent, `scripts/`, first on its `sys.path`.
# This module answers that import with the real module under its new name.
#
# THERE IS NO `__init__.py` IN THIS DIRECTORY, ON PURPOSE. Without one, this
# directory is a portion of the `ideation_dashboard` NAMESPACE package, so in a
# composed run it merges with openxFactory's own `scripts/ideation_dashboard/`
# (which has none either) instead of shadowing it. An `__init__.py` here would
# turn `ideation_dashboard` into a regular package and hide every openxFactory
# lane module beside it.
#
# `sys.modules[__name__] = _m` replaces this module's own entry with the real
# one, so `ideation_dashboard.session_git` and `opendox.session_git` are the
# same module object, and `SessionGit` and the rest of its names are identical.
import sys

from opendox import session_git as _m

sys.modules[__name__] = _m
