import re
import subprocess
import sys
from pathlib import Path

import yaml

GITHUB_SHA = re.compile(r"[^@\s]+/[^@\s]+@[0-9a-fA-F]{40}\Z")
DOCKER_DIGEST = re.compile(r"docker://[^@\s]+@sha256:[0-9a-fA-F]{64}\Z", re.IGNORECASE)


def check_reference(reference: object, location: str, errors: list[str]) -> None:
    if isinstance(reference, str):
        if reference.startswith("./"):
            return
        pattern = (
            DOCKER_DIGEST if reference.lower().startswith("docker://") else GITHUB_SHA
        )
        if pattern.fullmatch(reference):
            return
    errors.append(
        f"{location}: {reference!r} must pin a full commit SHA or Docker SHA-256 digest"
    )


def check_steps(
    steps: list[dict[str, object]], location: str, errors: list[str]
) -> None:
    for index, step in enumerate(steps):
        if "uses" in step:
            check_reference(step["uses"], f"{location}[{index}].uses", errors)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
        )
        .decode()
        .split("\0")
    )
    errors = []
    checked = 0
    for name in sorted(set(paths)):
        path = Path(name)
        workflow = (
            path.parent.as_posix().lower() == ".github/workflows"
            and path.suffix.lower()
            in (
                ".yml",
                ".yaml",
            )
        )
        if not workflow and path.name.lower() not in ("action.yml", "action.yaml"):
            continue
        checked += 1
        try:
            document = yaml.safe_load((root / path).read_text())
        except yaml.YAMLError as error:
            errors.append(f"{name}: invalid YAML: {error}")
            continue
        if workflow:
            for job_name, job in document.get("jobs", {}).items():
                location = f"{name}:jobs.{job_name}"
                if "uses" in job:
                    check_reference(job["uses"], f"{location}.uses", errors)
                check_steps(job.get("steps", []), f"{location}.steps", errors)
        if path.name.lower() in ("action.yml", "action.yaml"):
            runs = document.get("runs", {})
            check_steps(runs.get("steps", []), f"{name}:runs.steps", errors)
            image = runs.get("image")
            if isinstance(image, str) and image.lower().startswith("docker://"):
                check_reference(image, f"{name}:runs.image", errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Action pins: {checked} workflow/action definitions passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
