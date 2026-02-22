from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
import tempfile

@dataclass(frozen=True)
class Target:
    key: str
    title: str
    path: Path
    requires_admin: bool = False

def list_targets() -> list[Target]:
    targets: list[Target] = []

    user_temp = Path(tempfile.gettempdir())
    targets.append(Target("user", "User TEMP (%TEMP%)", user_temp, requires_admin=False))

    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    targets.append(Target("system", "System TEMP (C:\\Windows\\Temp)", system_root / "Temp", requires_admin=True))
    targets.append(Target("prefetch", "Prefetch (C:\\Windows\\Prefetch)", system_root / "Prefetch", requires_admin=True))

    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        targets.append(Target("localtemp", "LocalAppData Temp (%LOCALAPPDATA%\\Temp)", Path(localapp) / "Temp", requires_admin=False))

    # Deduplicate same resolved paths
    seen: set[Path] = set()
    uniq: list[Target] = []
    for t in targets:
        try:
            rp = t.path.resolve()
        except Exception:
            rp = t.path
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(t)
    return uniq
