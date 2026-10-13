import unittest
from cases import GOOD, FAULTS, REQUEST, EXPECTED
from template_judge import judge, STAGES
from retry_loop import run_with_retries


class JudgeTests(unittest.TestCase):
    def test_reference_template_passes_all_stages(self):
        v = judge(GOOD, REQUEST, EXPECTED)
        self.assertTrue(v.passed, v.message)
        self.assertEqual(v.stage_reached, 4)

    def test_each_fault_fails_at_the_expected_stage(self):
        for name, (template, stage) in FAULTS.items():
            with self.subTest(name):
                v = judge(template, REQUEST, EXPECTED)
                self.assertEqual(v.failed_stage, stage, f"{name}: {v.message}")
                self.assertEqual(v.stage_reached, STAGES.index(stage))


class RetryTests(unittest.TestCase):
    def test_retry_loop_repairs_a_fault(self):
        broken = FAULTS["wrong command"][0]
        calls = []

        def fake_llm(prompt):
            calls.append(prompt)
            return GOOD

        v, attempts = run_with_retries("configure eth0", REQUEST, EXPECTED, fake_llm, broken)
        self.assertTrue(v.passed)
        self.assertEqual(attempts, 2)
        self.assertIn("execute", calls[0])

    def test_gives_up_after_max_retries(self):
        broken = FAULTS["wrong command"][0]
        v, attempts = run_with_retries("t", REQUEST, EXPECTED, lambda p: broken, broken,
                                       max_retries=2)
        self.assertFalse(v.passed)
        self.assertEqual(attempts, 3)


if __name__ == "__main__":
    unittest.main()
