from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import time
import shutil

@dataclass
class CleanStats:
    scanned_files: int = 0
    scanned_dirs: int = 0
    deleted_files: int = 0
    deleted_dirs: int = 0
    skipped: int = 0
    errors: int = 0
    bytes_freed: int = 0

@dataclass(frozen=True)
class CleanOptions:
    older_days: int = 1
    dry_run: bool = True
    include_dirs: bool = True
    skip_prefixes: tuple[str, ...] = ("pip-", "uv-", "npm-", "pnpm-", "yarn-", "TempCleaner-", "JetBrains", "CrashDumps")

def _is_older_than(path: Path, cutoff_ts: float) -> bool:
    try:
        return path.stat().st_mtime < cutoff_ts
    except Exception:
        return False

def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0

def _safe_unlink(path: Path) -> bool:
    try:
        try:
            os.chmod(path, 0o666)
        except Exception:
            pass
        path.unlink(missing_ok=True)
        return True
    except Exception:
        return False

def _safe_rmtree(path: Path) -> bool:
    try:
        def onerror(func, p, excinfo):
            try:
                os.chmod(p, 0o777)
                func(p)
            except Exception:
                pass
        shutil.rmtree(path, onerror=onerror)
        return True
    except Exception:
        return False

def clean_path(root: Path, opts: CleanOptions, log_cb=None) -> CleanStats:
    stats = CleanStats()
    if log_cb is None:
        log_cb = lambda s: None  # noqa

    root = root.expanduser()

    if not root.exists():
        log_cb(f"[skip] Not found: {root}")
        stats.skipped += 1
        return stats
    if not root.is_dir():
        log_cb(f"[skip] Not a directory: {root}")
        stats.skipped += 1
        return stats

    cutoff_ts = time.time() - (max(0, int(opts.older_days)) * 86400)
    log_cb(f"[scan] {root} (older_days={opts.older_days}, dry_run={opts.dry_run})")

    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        d = Path(dirpath)
        stats.scanned_dirs += 1

        if any(d.name.startswith(x) for x in opts.skip_prefixes):
            stats.skipped += 1
            continue

        for fn in filenames:
            fp = d / fn
            stats.scanned_files += 1

            if fp.name.startswith("TempCleaner-"):
                stats.skipped += 1
                continue

            if opts.older_days > 0 and not _is_older_than(fp, cutoff_ts):
                stats.skipped += 1
                continue

            size = _file_size(fp)
            if opts.dry_run:
                log_cb(f"  [dry] delete file: {fp}")
                stats.bytes_freed += size
                stats.deleted_files += 1
            else:
                if _safe_unlink(fp):
                    log_cb(f"  [ok]  deleted file: {fp}")
                    stats.bytes_freed += size
                    stats.deleted_files += 1
                else:
                    stats.errors += 1
                    log_cb(f"  [err] failed file: {fp}")

        if opts.include_dirs:
            try:
                if not any(d.iterdir()):
                    if opts.older_days > 0 and not _is_older_than(d, cutoff_ts):
                        stats.skipped += 1
                        continue

                    if opts.dry_run:
                        log_cb(f"  [dry] delete dir : {d}")
                        stats.deleted_dirs += 1
                    else:
                        if _safe_rmtree(d):
                            log_cb(f"  [ok]  deleted dir : {d}")
                            stats.deleted_dirs += 1
                        else:
                            stats.errors += 1
                            log_cb(f"  [err] failed dir : {d}")
            except Exception:
                stats.errors += 1
                log_cb(f"  [err] failed scan dir: {d}")

    return stats
