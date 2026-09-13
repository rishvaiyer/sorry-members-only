"""Optional hard execution runtime for agent workers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import subprocess
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """Safe metadata about one isolated command attempt."""

    completed: bool
    exit_code: int | None
    reason: str
    timed_out: bool = False


class SandboxRuntime(Protocol):
    """Small seam for Docker, a VM, or another host-enforced runtime."""

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: float = 10.0,
    ) -> SandboxResult:
        """Run a command inside an isolated execution environment."""
        ...


class SandboxRuntimeDenied(PermissionError):
    """Raised when the hard runtime refuses or cannot run a command."""

    def __init__(self, result: SandboxResult) -> None:
        super().__init__(result.reason)
        self.result = result


class DockerSandbox:
    """Run a command in a restrictive Docker container.

    The image must already exist locally. This class never pulls images,
    mounts host paths, forwards environment variables, or enables networking.
    """

    def __init__(
        self,
        *,
        image: str,
        docker_binary: str = "docker",
    ) -> None:
        if not image.strip() or image.startswith("-") or any(char.isspace() for char in image):
            raise ValueError("image must be a non-empty image reference")
        if not docker_binary.strip():
            raise ValueError("docker_binary must be a non-empty string")
        self._image = image
        self._docker_binary = docker_binary

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: float = 10.0,
    ) -> SandboxResult:
        """Run without shell expansion and fail closed on runtime errors."""

        if not command or any(
            not isinstance(part, str) or not part for part in command
        ):
            raise ValueError("command must contain non-empty strings")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        argv = [
            self._docker_binary,
            "run",
            "--pull=never",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--pids-limit=64",
            "--memory=128m",
            "--cpus=1.0",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--user=65532:65532",
            "--workdir=/tmp",
            self._image,
            *command,
        ]

        try:
            completed = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return SandboxResult(False, None, "runtime_unavailable")
        except subprocess.TimeoutExpired:
            return SandboxResult(False, None, "runtime_timeout", timed_out=True)
        except OSError:
            return SandboxResult(False, None, "runtime_error")

        if completed.returncode == 0:
            return SandboxResult(True, 0, "completed")
        return SandboxResult(False, completed.returncode, "runtime_rejected")
