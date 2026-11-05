import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
BASE = "jobs:\n  lint:\n    runs-on: ubuntu-latest\n    steps:\n"


class ActionPinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        self.script = self.root / ".github/scripts/check-action-pins.py"
        self.script.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).with_name("check-action-pins.py"), self.script)
        self.workflow = self.root / ".github/workflows/test.yml"
        self.workflow.parent.mkdir()

    def assert_check(self, passes: bool, error: str = "must pin") -> None:
        result = subprocess.run(
            [sys.executable, str(self.script)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0 if passes else 1, result.stderr)
        if not passes:
            self.assertIn(error, result.stderr)
            self.assertRegex(result.stderr, r"(?im)^.*\.ya?ml:")
            self.assertNotIn("Traceback", result.stderr)

    def test_workflow_references(self) -> None:
        cases = [
            ("actions/checkout@v7", False),
            ("actions/checkout@main", False),
            ("actions/checkout@3d3c42e", False),
            (f"actions/checkout@release-{SHA}", False),
            (f"actions/checkout@{SHA}", True),
            (f"actions/checkout@{SHA.upper()}", True),
            ("./.github/actions/local", True),
            ("docker://ghcr.io/org/img:latest", False),
            ("docker://ghcr.io/org/img@sha256:" + "a" * 64, True),
            ("docker://ghcr.io/org/img@sha256:" + "a" * 63, False),
        ]
        for reference, passes in cases:
            for step in (
                f'      - uses: "{reference}"\n',
                f'      - {{uses: "{reference}"}}\n',
            ):
                with self.subTest(reference=reference, step=step):
                    self.workflow.write_text(BASE + step)
                    self.assert_check(passes)

    def test_yaml_forms_and_reusable_workflows(self) -> None:
        cases = [
            (BASE + "      - uses: >-\n          actions/checkout@main\n", False),
            (
                "env: &s {uses: actions/checkout@main}\n" + BASE + "      - <<: *s\n",
                False,
            ),
            (BASE + "      - &s {uses: actions/checkout@main}\n      - *s\n", False),
            (
                "jobs:\n  lint:\n    uses: owner/repo/.github/workflows/ci.yml@v1\n",
                False,
            ),
            (
                "jobs:\n  lint:\n    uses: "
                f"owner/repo/.github/workflows/ci.yml@{SHA}\n",
                True,
            ),
            (
                BASE
                + f"      - uses: actions/checkout@{SHA}\n"
                + "        with:\n          uses: data\n",
                True,
            ),
            ("jobs: [broken\n", False),
        ]
        for text, passes in cases:
            with self.subTest(text=text):
                self.workflow.write_text(text)
                error = "invalid YAML" if text == "jobs: [broken\n" else "must pin"
                self.assert_check(passes, error)

    def test_nested_actions_and_tracked_ignored_files(self) -> None:
        self.workflow.write_text(BASE + "      - run: echo ok\n")
        action = self.root / "a/b/c/d/e/f/action.yaml"
        action.parent.mkdir(parents=True)
        cases = [
            ("runs:\n  using: docker\n  image: DOCKER://node:latest\n", False),
            (
                "runs:\n  using: docker\n  image: DOCKER://node@sha256:"
                + "a" * 64
                + "\n",
                True,
            ),
            (
                "runs:\n  using: Composite\n  steps:\n    - uses: owner/repo@main\n",
                False,
            ),
            (
                f"runs:\n  using: composite\n  steps:\n    - uses: owner/repo@{SHA}\n",
                True,
            ),
            ("runs:\n  using: Docker\n  image: docker://node:latest\n", False),
            (
                "runs:\n  using: docker\n  image: docker://node@sha256:"
                + "a" * 64
                + "\n",
                True,
            ),
            ("runs:\n  using: docker\n  image: Dockerfile\n", True),
        ]
        for text, passes in cases:
            with self.subTest(text=text):
                action.write_text(text)
                self.assert_check(passes)
        subprocess.run(["git", "add", "-f", str(action)], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("a/\n")
        action.write_text(cases[0][0])
        self.assert_check(False)

    def test_action_filename_in_workflow_directory(self) -> None:
        self.workflow.write_text(BASE + "      - run: echo ok\n")
        for filename in ("action.yml", "Action.YAML"):
            action = self.workflow.with_name(filename)
            for text, passes in [
                (
                    "runs:\n  using: Composite\n  steps:\n"
                    "    - uses: owner/repo@main\n",
                    False,
                ),
                (
                    "runs:\n  using: composite\n  steps:\n"
                    f"    - uses: owner/repo@{SHA}\n",
                    True,
                ),
                ("runs:\n  using: docker\n  image: DOCKER://node:latest\n", False),
                ("runs:\n  using: docker\n  image: Dockerfile\n", True),
            ]:
                with self.subTest(filename=filename, text=text):
                    action.write_text(text)
                    self.assert_check(passes)
            action.unlink()


if __name__ == "__main__":
    unittest.main()
