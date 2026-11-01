"""G3c seed derivation (charter section 3). usage: seed.py BEACON_JSON FREEZE_JSON. Standard library only."""
import hashlib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release import CHARTER, FREEZE  # noqa: E402

beacon = json.load(open(sys.argv[1], encoding="utf-8")); fz = json.load(open(sys.argv[2], encoding="utf-8"))
subprocess.check_call(["git", "diff", "--quiet", fz["freeze_sha"], "HEAD", "--", ".", f":!{FREEZE}"])  # whole tree must equal the freeze
charter = subprocess.check_output(["git", "show", f"{fz['freeze_sha']}:{CHARTER}"])
m = re.search(rb"drand quicknet round R = (\d+)", charter)
assert m and int(m.group(1)) == fz["R"] == beacon["round"], "round in charter / FREEZE.json / beacon disagree"
assert beacon["bls_verified"] is True
ch = hashlib.sha256(charter).hexdigest()
sb = int(hashlib.sha256((ch + beacon["randomness"].lower()).encode("ascii")).hexdigest()[:16], 16)
print(json.dumps({"seed_base": sb, "charter_sha256": ch, "R": fz["R"], "freeze_sha": fz["freeze_sha"]}))
