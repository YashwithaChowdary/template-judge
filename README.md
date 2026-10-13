# Staged Judge for Device Configuration Templates

A small Python prototype for checking whether a candidate configuration template is actually correct, not just plausible. It is a toy version of the evaluation idea for generative AI that writes network device templates.

A template turns a high-level request (interface, IP address, VLANs) into the exact commands a device needs. The judge checks a candidate in four increasingly demanding stages and reports how far it got:

| Stage | Check |
|---|---|
| 1. Format | template syntax is valid (balanced loops, known tags) |
| 2. Render | it renders against the request without errors |
| 3. Execute | the commands run on a simulated device (toy router CLI) |
| 4. Correct | the final device state matches the request |

`cases.py` holds one correct template and five faulty variants with known fixes, such as an unclosed loop, an undefined variable, a wrong command, and a forgotten `no shutdown`.

## Run

    python demo.py
    python -m unittest test_template_judge.py

## Feedback-driven retries

`retry_loop.py` sends the failure message back to a model and tries again. Tests use a fake model. `llm_experiment.py` runs it with a real model (set `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`) and writes `results.md`.

## Status

Prototype. The template language and device are toys, and the checks are hand-written. `llm_experiment.py` has not been run with published results yet.
