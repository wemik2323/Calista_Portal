import os
import subprocess
from dataclasses import dataclass


@dataclass
class SSHResult:
    ok: bool
    output: str
    error: str = ""


class WindowsSSHClient:
    def __init__(self):
        self.host = os.getenv("KIDS_PC_HOST", "")
        self.user = os.getenv("KIDS_PC_USER", "")
        self.key = os.getenv("KIDS_PC_SSH_KEY", "")
        self.port = os.getenv("KIDS_PC_SSH_PORT", "22")

    def _base_cmd(self) -> list[str]:
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-p",
            str(self.port),
        ]
        if self.key:
            cmd += ["-i", self.key]
        cmd += [f"{self.user}@{self.host}"]
        return cmd

    def run(self, remote_command: str) -> SSHResult:
        if not self.host or not self.user:
            return SSHResult(False, "", "Не настроены KIDS_PC_HOST / KIDS_PC_USER")

        cmd = self._base_cmd() + [remote_command]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=False,
                timeout=15,
                check=False,
            )

            stdout = completed.stdout.decode(
                "cp1251",
                errors="replace",
            ).strip()

            stderr = completed.stderr.decode(
                "cp1251",
                errors="replace",
            ).strip()

            return SSHResult(
                ok=completed.returncode == 0,
                output=stdout,
                error=stderr,
            )

        except subprocess.TimeoutExpired:
            return SSHResult(False, "", "Таймаут SSH")
        except Exception as e:  # noqa: BLE001
            return SSHResult(False, "", str(e))

    def is_online(self) -> bool:
        result = self.run("echo OK")
        return result.ok and "OK" in result.output

    def lock(self) -> SSHResult:
        return self.run("rundll32.exe user32.dll,LockWorkStation")

    def shutdown(self) -> SSHResult:
        return self.run("shutdown /s /t 0")

    def reboot(self) -> SSHResult:
        return self.run("shutdown /r /t 0")

    def notify(self, text: str) -> SSHResult:
        safe = text.replace('"', "'")
        return self.run(f'powershell -NoProfile -Command "msg * /time:30 \\"{safe}\\""')

    def list_processes(self) -> SSHResult:
        return self.run(
            "powershell -NoProfile -Command "
            '"$OutputEncoding = [System.Text.UTF8Encoding]::new(); '
            "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); "
            "Get-Process | "
            "Sort-Object WorkingSet -Descending | "
            "Select-Object -First 30 ProcessName,Id,WorkingSet | "
            "ForEach-Object { "
            "$_.ProcessName + '|' + $_.Id + '|' + "
            "[int]($_.WorkingSet/1MB) "
            '}"'
        )

    def kill_pid(self, pid: int) -> SSHResult:
        return self.run(f"taskkill /PID {int(pid)} /F")

    def kill_name(self, name: str) -> SSHResult:
        safe = name.replace('"', "")
        return self.run(f'taskkill /IM "{safe}" /F')
