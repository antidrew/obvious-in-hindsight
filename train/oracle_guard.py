"""Keep oracle runs out of training data (reports/rethink-2026-11-02/ceilings.md section 4, assertion 3).

Oracle logs hold gold text in their prompts, and an adapter trained on them could not be scanned afterwards. Both
builders refuse by path (results/*oracle*, research/, symlinks followed) and by content (the section header written
by scripts/build_oracle_data.py), so that a renamed or copied log is still caught.
"""
import os, re, sys

BAD_PATH = re.compile(r"(^|/)research/|oracle", re.I)
ORACLE_HEADER = "## Verified information for this task"


def check_path(path):
    for p in (str(path), os.path.realpath(path)):
        if BAD_PATH.search(p):
            sys.exit(f"REFUSED: {path} is oracle or research data and must never be used for training")


def check_record(rec):
    for m in rec.get("messages") or []:
        if m.get("role") == "user" and ORACLE_HEADER in str(m.get("content")):
            sys.exit(f"REFUSED: a logged call of {rec.get('instance_id')} carries an oracle section")
