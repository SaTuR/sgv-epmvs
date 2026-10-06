import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

BACKUP_DIR=Path(settings.upload_path)/"backups"
RCLONE_CONFIG=Path(settings.upload_path)/"rclone"/"rclone.conf"

def _db_url():
    return settings.database_url.replace("postgresql+psycopg://","postgresql://",1)

def _run(command:list[str],timeout:int=3600):
    result=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
    if result.returncode!=0:
        raise RuntimeError((result.stderr or result.stdout or "Comando falló").strip())
    return result.stdout

def rclone_config_present():
    return RCLONE_CONFIG.exists() and RCLONE_CONFIG.stat().st_size>0

def test_remote(remote_name:str):
    if not rclone_config_present():
        raise RuntimeError("No se ha cargado el archivo rclone.conf")
    if not remote_name.strip():
        raise RuntimeError("Debe configurar el nombre del remoto")
    _run(["rclone","lsd",f"{remote_name.strip()}:", "--config",str(RCLONE_CONFIG)],timeout=120)
    return True

def _remote_dir(remote_name:str,folder:str):
    folder=(folder or "").strip().strip("/")
    return f"{remote_name.strip()}:{folder}" if folder else f"{remote_name.strip()}:"

def _prune_remote(remote_name:str,folder:str,keep_last:int):
    remote_dir=_remote_dir(remote_name,folder)
    raw=_run(["rclone","lsjson",remote_dir,"--files-only","--config",str(RCLONE_CONFIG)],timeout=300)
    items=json.loads(raw or "[]")
    backups=[x for x in items if x.get("Name","").startswith("sgv_epmvs_") and x.get("Name","").endswith(".dump")]
    backups.sort(key=lambda x:x.get("ModTime",""),reverse=True)
    for item in backups[max(1,keep_last):]:
        _run(["rclone","deletefile",f"{remote_dir}/{item['Name']}","--config",str(RCLONE_CONFIG)],timeout=300)

def _prune_local(keep_last:int):
    files=sorted(BACKUP_DIR.glob("sgv_epmvs_*.dump"),key=lambda p:p.stat().st_mtime,reverse=True)
    for path in files[max(1,keep_last):]:
        path.unlink(missing_ok=True)

def run_backup(remote_name:str,folder:str,keep_last:int=2):
    if not rclone_config_present():
        raise RuntimeError("No se ha cargado el archivo rclone.conf")
    if not remote_name.strip():
        raise RuntimeError("Debe configurar el nombre del remoto")

    BACKUP_DIR.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename=f"sgv_epmvs_{stamp}.dump"
    local_path=BACKUP_DIR/filename

    _run([
        "pg_dump",
        "--format=custom",
        "--compress=9",
        "--no-owner",
        "--no-acl",
        "--file",str(local_path),
        _db_url(),
    ])

    remote_dir=_remote_dir(remote_name,folder)
    _run([
        "rclone","copyto",str(local_path),f"{remote_dir}/{filename}",
        "--config",str(RCLONE_CONFIG),
        "--retries","3",
        "--low-level-retries","10",
    ])

    _prune_remote(remote_name,folder,keep_last)
    _prune_local(keep_last)
    return filename
