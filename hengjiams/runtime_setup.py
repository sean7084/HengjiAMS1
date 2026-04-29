import os
from pathlib import Path


def load_local_env() -> None:
    """Load key=value pairs from the repo-local .env file into os.environ."""
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def configure_windows_fontconfig() -> None:
    """Provide a local Fontconfig config on Windows for WeasyPrint usage."""
    if os.name != "nt":
        return

    if os.environ.get("FONTCONFIG_FILE"):
        return

    project_root = Path(__file__).resolve().parent.parent
    fontconfig_dir = project_root / "runtime" / "fontconfig"
    fontconfig_file = fontconfig_dir / "fonts.conf"
    if not fontconfig_file.exists():
        return

    local_app_data = Path(os.environ.get("LOCALAPPDATA", str(project_root)))
    cache_home = local_app_data / "hengjiams-fontconfig-cache"
    cache_home.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("XDG_CACHE_HOME", str(cache_home))
    os.environ.setdefault("FONTCONFIG_PATH", str(fontconfig_dir))
    os.environ.setdefault("FONTCONFIG_FILE", str(fontconfig_file))
