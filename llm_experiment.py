"""
Ask a real model to write the template, judge it, and retry with feedback.

    set GEMINI_API_KEY=...   (or ANTHROPIC_API_KEY)
    py llm_experiment.py

Records, per retry budget (0-3), how far each attempt gets. Output: results.md
"""
from cases import REQUEST, EXPECTED
from llm_client import ask_llm
from retry_loop import run_with_retries
from template_judge import judge, STAGES

TASK = ("Write a device configuration template in this small language: "
        "{{ name }} substitutes a request value, and "
        "{% for v in list %} ... {% endfor %} repeats lines. "
        "Device commands: 'interface <name>', 'ip address <ip> <mask>', "
        "'no shutdown', 'switchport trunk allowed vlan add <n>', 'exit'. "
        "Request keys: interface, ip, mask, vlans (a list). "
        "Configure the interface with the address, bring it up, and allow every VLAN. "
        "Reply with only the template.")

if __name__ == "__main__":
    rows = []
    for budget in range(0, 4):
        first = ask_llm(TASK).strip()
        verdict, attempts = run_with_retries(TASK, REQUEST, EXPECTED, ask_llm, first, budget)
        rows.append((budget, attempts, verdict.stage_reached, verdict.passed))
        print(f"retries allowed {budget}: attempts {attempts}, stages {verdict.stage_reached}/4")
    lines = ["# Results", "", "| Retries allowed | Attempts used | Stages passed | Passed |",
             "|---|---|---|---|"]
    lines += [f"| {b} | {a} | {s}/{len(STAGES)} | {p} |" for b, a, s, p in rows]
    open("results.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("Saved results.md")
