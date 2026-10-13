"""Feedback-driven retries: judge a template, send the failure to a model, retry."""
from template_judge import judge


def repair_prompt(task, template, verdict):
    return (f"Task: {task}\nYour template:\n{template}\n"
            f"It failed the '{verdict.failed_stage}' check: {verdict.message}\n"
            "Reply with only the corrected template.")


def run_with_retries(task, request, expected, llm, first_template, max_retries=3):
    """Returns (final_verdict, attempts). `llm` is any function: prompt -> text."""
    template = first_template
    verdict = judge(template, request, expected)
    attempts = 1
    while not verdict.passed and attempts <= max_retries:
        template = llm(repair_prompt(task, template, verdict)).strip()
        verdict = judge(template, request, expected)
        attempts += 1
    return verdict, attempts
