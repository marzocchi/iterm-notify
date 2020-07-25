from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Command:
    started_at: datetime
    command_line: str

    def complete(self, exit_code: int, finished_at: datetime) -> 'CompleteCommand':
        return CompleteCommand(command=self, duration=finished_at - self.started_at, exit_code=exit_code)


@dataclass(frozen=True)
class CompleteCommand:
    command: Command
    duration: timedelta
    exit_code: int

    @property
    def successful(self) -> bool:
        return self.exit_code == 0
