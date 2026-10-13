"""Run the judge on the reference template and every faulty variant."""
from cases import GOOD, FAULTS, REQUEST, EXPECTED
from template_judge import judge, STAGES

print(f"{'Template':28} {'Stages passed':14} Result")
cases = [("reference (correct)", GOOD)] + [(n, t) for n, (t, _) in FAULTS.items()]
for name, template in cases:
    v = judge(template, REQUEST, EXPECTED)
    print(f"{name:28} {v.stage_reached}/{len(STAGES):<12} "
          f"{'PASS' if v.passed else 'FAIL at ' + v.failed_stage + ': ' + v.message}")
