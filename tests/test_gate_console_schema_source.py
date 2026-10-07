"""The gate console's contract schemas, each read where its owner keeps it
(plan 038 T021, U-2; R2Q8 (a); P4F-4, ruled with plan 038 on openxFactory#656
comment 6013547504; R1Q27 (a), comment 5851950767).

`openxdox.gate_console` validates two documents against two schemas with two
owners:
  * a gate-action record, against openXdox-spec's schema, which this
    distribution packages (`openxdox.contracts`, held to its digest by
    `copies.yaml`). The console reads it from there;
  * a demotion execution receipt, against openxFactory's schema, which nothing
    here vendors. The console reads it from the source a host registers with
    `register_contract_schema_source()`, and with none registered it refuses,
    naming that call.

THESE CASES RUN IN A LONE CHECKOUT, so in F9.1 and in the required job. The
console imports openxFactory's `doc_health` when it loads (R1Q6 (d)'s reason),
though nothing these cases run calls it. So each case runs the console in a
CHILD interpreter, beside a stand-in `doc_health` that answers the three names
the console's import reads and nothing else. This process never imports the
console through the stand-in. The child's import path is set whole, so in a
composed run openxFactory's `doc_health` is not on it either, and no source is
registered there unless the case registers one.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src"
GATE_CONSOLE = SOURCE / "openxdox" / "gate_console.py"

#: The names the console's import reads from `doc_health`: `corpus` for
#: `STATUS_SCAN_LINES` (gate_console.py), and `lines` for `split_keepends` and
#: `join_rows` (round_trip.py). Nothing these cases run calls either function.
_STAND_IN = {
    "__init__.py": "",
    "corpus.py": "STATUS_SCAN_LINES = 0\n",
    "lines.py": ("def split_keepends(text):\n"
                 "    raise AssertionError('the doc_health stand-in')\n\n\n"
                 "def join_rows(rows):\n"
                 "    raise AssertionError('the doc_health stand-in')\n"),
}

#: Run first in every child: the console, a valid gate-action record and a
#: receipt, and `refusal()`, which answers None where the call passes and the
#: refusal's type and words where it refuses.
_PRELUDE = '''
import json
import shutil
import sys
from pathlib import Path

from openxdox import contracts
from openxdox import gate_console as gc

out = {}
RECORD = gc.build_gate_action_record(
    actor="brett", action="demote", at="2026-10-06T00:00:00Z", reason="why",
    change_id="add-x", artifacts=[{"kind": "transition-manifest",
                                   "reference": "ideation/staging/x/m.yaml"}])
RECEIPT = {"kind": "from-a", "destination": {"id": "x", "path": "ideation/staging/x"},
           "transition_manifest": "ideation/staging/x/m.yaml"}


def refusal(call, *args):
    try:
        call(*args)
    except (gc.GateRefused, gc.ContractSchemaSourceRefused) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None
'''


def _in_a_child(tmp_path: Path, body: str) -> dict:
    """Run `body` after the prelude in a fresh interpreter whose import path is
    the `doc_health` stand-in and this checkout's `src/`, and answer the
    `out` mapping it prints."""
    stand_in = tmp_path / "stand-in" / "doc_health"
    stand_in.mkdir(parents=True)
    for name, text in _STAND_IN.items():
        (stand_in / name).write_text(text, encoding="utf-8")
    script = tmp_path / "case.py"
    script.write_text(_PRELUDE + textwrap.dedent(body)
                      + "\nprint(json.dumps(out))\n", encoding="utf-8")
    env = {key: value for key, value in os.environ.items()
           if key != "PYTHONPATH"}
    env["PYTHONPATH"] = os.pathsep.join((str(stand_in.parent), str(SOURCE)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run([sys.executable, str(script)], cwd=tmp_path, env=env,
                         capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout.splitlines()[-1])


def _receipt_source(directory: Path, *, kind: str, extra: dict | None = None) -> Path:
    """A host's contract schema directory, stood in: its receipt schema admits
    one `kind`. `extra` adds further schema files beside it."""
    directory.mkdir(parents=True)
    schema = {"type": "object", "required": ["kind", "destination"],
              "properties": {"kind": {"const": kind}}}
    (directory / "demotion-execution-receipt.schema.yaml").write_text(
        json.dumps(schema), encoding="utf-8")
    for name, text in (extra or {}).items():
        (directory / name).write_text(text, encoding="utf-8")
    return directory


def test_a_receipt_refuses_by_name_where_no_host_registered_its_schema(tmp_path) -> None:
    out = _in_a_child(tmp_path, '''
        out["registered"] = gc.contract_schema_source_registered()
        out["refusal"] = refusal(gc.validate_demotion_execution_receipt, RECEIPT)
    ''')
    assert out["registered"] is False
    assert out["refusal"].startswith("GateRefused: the demotion execution receipt cannot be validated")
    assert "demotion-execution-receipt.schema.yaml" in out["refusal"]
    assert ("openxdox.gate_console.register_contract_schema_source(<directory>)"
            in out["refusal"])


def test_a_gate_action_record_is_read_from_the_packaged_copy(tmp_path) -> None:
    """With no source registered the record validates; a record the schema
    does not admit refuses; a registered source whose own record schema admits
    nothing is never read for a record; and a packaged copy that drifted from
    its digest refuses."""
    hostile = _receipt_source(tmp_path / "hostile", kind="from-a", extra={
        "gate-action-record.schema.yaml": json.dumps({"not": {}})})
    out = _in_a_child(tmp_path, f'''
        out["valid"] = refusal(gc.validate_gate_action_record, RECORD)
        out["not_admitted"] = refusal(gc.validate_gate_action_record,
                                      dict(RECORD, kind="another-kind"))
        gc.register_contract_schema_source({str(hostile)!r})
        out["beside_a_hostile_source"] = refusal(gc.validate_gate_action_record, RECORD)
        staged = Path({str(tmp_path / "staged")!r})
        shutil.copytree(contracts.package_dir(), staged,
                        ignore=shutil.ignore_patterns("__pycache__", "*.py"))
        drifted = staged / "schemas" / "gate-action-record.schema.yaml"
        drifted.write_bytes(drifted.read_bytes() + b"\\n")
        contracts.package_dir = lambda: staged
        out["drifted"] = refusal(gc.validate_gate_action_record, RECORD)
    ''')
    assert out["valid"] is None
    assert out["not_admitted"].startswith(
        "GateRefused: the gate-action record failed schema validation: kind")
    assert out["beside_a_hostile_source"] is None
    assert out["drifted"].startswith(
        "GateRefused: the gate-action record schema could not be read from "
        "openXdox's packaged copy")
    assert "is not the spec leg's file" in out["drifted"]


def test_a_receipt_is_validated_against_the_registered_sources_schema(tmp_path) -> None:
    source = _receipt_source(tmp_path / "host" / "contracts" / "schemas", kind="from-a")
    out = _in_a_child(tmp_path, f'''
        out["returned"] = str(gc.register_contract_schema_source({str(source)!r}))
        out["registered"] = gc.contract_schema_source_registered()
        out["valid"] = refusal(gc.validate_demotion_execution_receipt, RECEIPT)
        out["not_admitted"] = refusal(gc.validate_demotion_execution_receipt,
                                      dict(RECEIPT, kind="from-b"))
    ''')
    assert out["returned"] == str(source.resolve())
    assert out["registered"] is True
    assert out["valid"] is None
    assert out["not_admitted"].startswith(
        "GateRefused: the demotion execution receipt failed schema validation: kind")


def test_the_seam_holds_one_source_and_refuses_a_second(tmp_path) -> None:
    first = _receipt_source(tmp_path / "a", kind="from-a")
    second = _receipt_source(tmp_path / "b", kind="from-b")
    empty = tmp_path / "c"
    empty.mkdir()
    out = _in_a_child(tmp_path, f'''
        out["first"] = str(gc.register_contract_schema_source(Path({str(first)!r})))
        out["again"] = str(gc.register_contract_schema_source({str(first)!r} + "/."))
        out["second"] = refusal(gc.register_contract_schema_source, {str(second)!r})
        out["still_first"] = refusal(gc.validate_demotion_execution_receipt, RECEIPT)
        gc.unregister_contract_schema_source()
        out["after_unregister"] = gc.contract_schema_source_registered()
        out["swapped"] = str(gc.register_contract_schema_source({str(second)!r}))
        out["now_second"] = refusal(gc.validate_demotion_execution_receipt,
                                    dict(RECEIPT, kind="from-b"))
        gc.unregister_contract_schema_source()
        out["no_schema"] = refusal(gc.register_contract_schema_source, {str(empty)!r})
        out["after_no_schema"] = gc.contract_schema_source_registered()
    ''')
    assert out["first"] == out["again"] == str(first.resolve())
    assert out["second"].startswith(
        "ContractSchemaSourceRefused: a contract schema source is already registered")
    assert str(first.resolve()) in out["second"] and str(second.resolve()) in out["second"]
    assert out["still_first"] is None
    assert out["after_unregister"] is False
    assert out["swapped"] == str(second.resolve())
    assert out["now_second"] is None
    assert out["no_schema"].startswith(
        f"ContractSchemaSourceRefused: {empty.resolve()} holds no "
        "demotion-execution-receipt.schema.yaml")
    assert out["after_no_schema"] is False


def test_a_host_schema_the_console_cannot_apply_refuses_as_gate_refused(tmp_path) -> None:
    """A registered source whose receipt schema the safe loader cannot read,
    is empty, is not a valid JSON Schema, or cannot be applied refuses as
    `GateRefused`, never as another exception. The demotion verb writes its
    receipt after it has moved files, and reports only a `GateRefused` there
    as a receipt not written (Copilot on #40: r4194497045; r4197914632, the
    loader raises `RecursionError` and `ValueError` past `YAMLError`;
    r4198638746, a cyclic alias the meta-schema check cannot finish)."""
    sources = {}
    for name, text in {"empty": "", "not_a_schema": "required: 1\n",
                       "unresolvable": json.dumps({"$ref": "#/$defs/absent"}),
                       "not_yaml": "type: [object\n",
                       "too_deep": "[" * 5000 + "]" * 5000,
                       "impossible_date": "type: object\nx: 2001-02-30\n",
                       "cyclic_mapping": "properties: &p {a: {properties: *p}}\n",
                       "cyclic_list": "allOf: &loop [*loop]\n"}.items():
        directory = tmp_path / name
        directory.mkdir()
        (directory / "demotion-execution-receipt.schema.yaml").write_text(
            text, encoding="utf-8")
        sources[name] = str(directory)
    out = _in_a_child(tmp_path, f'''
        for name, source in {sources!r}.items():
            gc.unregister_contract_schema_source()
            gc.register_contract_schema_source(source)
            try:
                gc.validate_demotion_execution_receipt(RECEIPT)
                out[name] = None
            except gc.GateRefused as exc:
                out[name] = f"GateRefused: {{exc}}"
            except Exception as exc:
                out[name] = f"ESCAPED {{type(exc).__name__}}: {{exc}}"
    ''')
    for name in ("empty", "not_a_schema"):
        assert out[name].startswith(
            "GateRefused: the demotion execution receipt schema is not a valid "
            "JSON Schema"), out[name]
    assert out["unresolvable"].startswith(
        "GateRefused: the demotion execution receipt schema could not be "
        "applied"), out["unresolvable"]
    for name in ("not_yaml", "too_deep", "impossible_date"):
        assert out[name].startswith(
            "GateRefused: the demotion execution receipt schema could not be "
            "parsed"), out[name]
    # A cyclic mapping and a cyclic list must each come out as a GateRefused,
    # and that is ALL these two assert. Which refusal each earns, and what it
    # wraps, is the installed jsonschema's own behaviour, and `pyproject.toml`
    # leaves it open (`jsonschema>=4.18`, no upper bound): the exception a
    # cyclic mapping raises from the meta-schema check, and whether the check
    # refuses a cyclic list itself, are not this console's contract. So neither
    # case names the step it was refused at or the exception it wraps. An
    # exception that ESCAPED reads `ESCAPED ...` and fails the prefix.
    for name in ("cyclic_mapping", "cyclic_list"):
        assert out[name].startswith("GateRefused: "), out[name]


def test_the_console_reads_no_schema_from_beside_the_checkout() -> None:
    """Before T021 both schemas were read from `parents[2]` of the module,
    which in this leg is the checkout root. No `parents` index is read in the
    console's code any more (its comments may still say where it was)."""
    tree = ast.parse(GATE_CONSOLE.read_text(encoding="utf-8"))
    reaches = [node.lineno for node in ast.walk(tree)
               if isinstance(node, ast.Subscript)
               and isinstance(node.value, ast.Attribute)
               and node.value.attr == "parents"]
    assert reaches == [], f"gate_console.py reads a parents index at lines {reaches}"
