# Branch protection: the `validate` check is required

Closes item 1.5 of `openxFactory openspec/changes/split-opendox-two-layer-product/tasks.md`
for this repository: *"Branch-protection ruleset created in EVALUATE mode in
each, promoted to ACTIVE once its required check has reported once."*

Ruleset state is a repository setting, not a tree fact: no check this
repository runs can read it, let alone assert it. This file is therefore the
evidence line 1.5 asks for.

It is added by the **OQ-O scaffold-levelling pass** (`opensoft/openxFactory#656`,
RULING of 2026-09-09: *"level the six scaffolds first, one small PR per repo"*).
The ruleset below has existed and been enforced since 2026-09-06; what was
missing was this file. The openDox family has carried its equivalent since the
day it was created, and an unlevel scaffold is how a carve failure gets
misdiagnosed as a scaffold difference.

## What exists

A **repository-level** ruleset (distinct from the two organization-sourced
rulesets `Require Code Owner Review` (id `18834180`) and `Copilot Auto-Review
All PRs` (id `8981805`), which were already in force before this project
existed and enforce PR-and-review, not any check content):

| field | value |
|---|---|
| name | `Require validate check` |
| id | `22371412` |
| target | `~DEFAULT_BRANCH` (`main`) |
| rule | `required_status_checks`, naming context `validate` |
| `strict_required_status_checks_policy` | `true` — see the note below |

## The EVALUATE → ACTIVE history

1. **Created in `evaluate`** on 2026-09-06 at 04:50Z, by the same lane that
   scaffolded this repository, recorded in `openxFactory#656` ("GROUP 1 —
   openXdox § 1.3 / 1.4 / 1.5 CLOSED OUT", 2026-09-06T04:51Z). `validate` had
   already reported SUCCESS on this repository's PRs #1 and #2.
2. **Promotion to `active` was OFFERED to Brett Heap, not performed** by the
   scaffolding lane — its hard limit was evaluate-only.
3. **Promoted to `active`** at 2026-09-06 08:56Z on his act; the
   `openxFactory#656` close-out of Group 1 records the end state as *"all six
   rulesets ACTIVE"*.

## The three repositories

The same ruleset exists, with the same rule, in all three repositories of the
`openxdox` project — the assembly root
[opensoft/openXdox](https://github.com/opensoft/openXdox) (id `22371409`), the
spec leg [opensoft/openXdox-spec](https://github.com/opensoft/openXdox-spec)
(id `22371411`) and the code leg
[opensoft/openXdox-code](https://github.com/opensoft/openXdox-code)
(id `22371412`) — and this file is added to all three by the same levelling
pass.

## One difference from the openDox family, RECORDED rather than changed

`strict_required_status_checks_policy` is **`true`** on all three openXdox-family
rulesets and **`false`** on all three openDox-family rulesets. Strict means a pull
request must be **up to date with `main`** before it can merge, so a branch
opened here needs a merge-from-`main` if anything lands first.

The levelling pass does **not** change it. A ruleset is a repository setting
outside any pull request's reach, and choosing which of the two policies the
family should standardise on is Brett Heap's act, not an author's. What the
pass owes is that the difference is written down where somebody hits it —
which is here, and in the PR that adds this file.
