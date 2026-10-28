"""Charter section 3 anti-seed-fishing checks.
usage: verify_anchor.py FREEZE_JSON [--rehearsal]
1. freeze_sha is the FIRST commit on main that introduced 'drand quicknet round R = <digits>' into the charter;
2. g3b/FREEZE.json touched by exactly one commit, a direct child of freeze_sha changing only that file;
3. the whole tree equals the freeze commit (except FREEZE.json);
4. no force-push to main has ever happened;
5. round R time >= 2 h after the freeze commit was pushed to main (GitHub server time).
--rehearsal (rehearsal/** branches): rules 1, 2 and 5 are checked against HEAD and its parent, not main."""
import datetime as dt, json, os, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release import CHARTER, FREEZE  # noqa: E402

CHAIN = "52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971"
fz = json.load(open(sys.argv[1])); REH = sys.argv[2:] == ["--rehearsal"]
if sys.argv[2:] not in ([], ["--rehearsal"]):
    sys.exit("usage: verify_anchor.py FREEZE_JSON [--rehearsal]")
git = lambda *a: subprocess.check_output(["git", *a], text=True).strip()


def fail(msg):
    sys.exit("FAIL: " + msg)


ref = "HEAD" if REH else "origin/main"
intro = git("log", "--reverse", "--format=%H", "-G", "drand quicknet round R = [0-9]+", ref, "--", CHARTER).split()
if not intro or intro[0] != fz["freeze_sha"]:
    fail(f"freeze_sha is not the first commit introducing the round line ({intro[:1]})")
cs = git("log", "--format=%H", ref, "--", FREEZE).split()
if len(cs) != 1:
    fail(f"{FREEZE} touched by {len(cs)} commits")
parents = git("rev-list", "--parents", "-n", "1", cs[0]).split()[1:]
changed = git("diff", "--name-only", fz["freeze_sha"], cs[0]).split()
if parents != [fz["freeze_sha"]] or changed != [FREEZE]:
    fail(f"FREEZE commit must be a direct child of freeze_sha changing only {FREEZE} ({parents}, {changed})")
if git("diff", "--name-only", fz["freeze_sha"], "HEAD", "--", ".", f":!{FREEZE}"):
    fail("tree differs from the freeze commit")
repo = os.environ.get("GITHUB_REPOSITORY", "mulaalig87-ops/xauusd-court-lab")
api = lambda q: json.loads(subprocess.check_output(["gh", "api", f"repos/{repo}/activity?ref=refs/heads/main&per_page=100&{q}"]))
if api("activity_type=force_push"):
    fail("force-push to main recorded")
info = json.load(urllib.request.urlopen(f"https://api.drand.sh/{CHAIN}/info", timeout=20))
rt = info["genesis_time"] + (fz["R"] - 1) * info["period"]
if REH:
    print(json.dumps({"rehearsal": True, "R": fz["R"], "round_time": rt}))
    print("anchor OK (REHEARSAL: rules 1-2 on HEAD; push-time rule 5 not applicable off main)")
    sys.exit(0)
ts = [dt.datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00")).timestamp()
      for a in api("activity_type=push") if a.get("after") == fz["freeze_sha"]]   # freeze must be the tip of its own push
if not ts:
    fail("freeze push not found in activity")
gap = (rt - min(ts)) / 3600
print(json.dumps({"freeze_sha": fz["freeze_sha"], "R": fz["R"], "round_time": rt, "push_time": min(ts), "gap_hours": round(gap, 3)}))
if gap < 2:
    fail("R less than 2 h after the freeze push")
print("anchor OK")
