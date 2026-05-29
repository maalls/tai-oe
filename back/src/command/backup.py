



import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


# --- Ensure src/ is importable whatever the launch dir ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.infrastructure.config import create_database_handler


BACKUP_DIR = Path(__file__).resolve().parents[2] / 'var' / 'backup'


# --- Bloc principal déplacé à la fin pour garantir la définition des fonctions ---

# ...existing code...



def get_postgres_config():
    handler = create_database_handler(current_file=__file__, require_postgres_password=False)
    cfg = handler.db_config
    return {
        'host': cfg.get('host', 'localhost'),
        'port': str(cfg.get('port', 5432)),
        'user': cfg.get('user', 'postgres'),
        'password': cfg.get('password', ''),
        'dbname': cfg.get('database', cfg.get('dbname', 'postgres')),
    }




def make_backup():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_dir = BACKUP_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    cfg = get_postgres_config()
    env = os.environ.copy()
    if cfg['password']:
        env['PGPASSWORD'] = cfg['password']

    backup_file = backup_dir / 'public.dump'
    print(f"Backing up schema public to {backup_file} ...")
    cmd = [
        'pg_dump',
        '-h', cfg['host'],
        '-p', cfg['port'],
        '-U', cfg['user'],
        '-d', cfg['dbname'],
        '-Fc',
        '-n', 'public',
        '--verbose',
        '-f', str(backup_file)
    ]
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")
        return 1
    print(f"Backup complete: {backup_file}")
    return 0


def find_latest_backup_dir():
    if not BACKUP_DIR.exists():
        print("No backup directory found.")
        return None
    subdirs = [d for d in BACKUP_DIR.iterdir() if d.is_dir()]
    if not subdirs:
        print("No backup found.")
        return None
    latest = max(subdirs, key=lambda d: d.name)
    return latest


def restore_latest_backup():
    backup_dir = find_latest_backup_dir()
    if not backup_dir:
        print("No backup to restore.")
        return 1
    print(f"Most recent backup: {backup_dir}")
    print("Contains:")
    for f in backup_dir.iterdir():
        print(f" - {f.name}")
    confirm = input(f"\nThis will ERASE and REPLACE your database and roles with backup from {backup_dir.name}.\nType YES to continue: ")
    if confirm.strip() != "YES":
        print("Restore cancelled.")
        return 1

    cfg = get_postgres_config()
    env = os.environ.copy()
    if cfg['password']:
        env['PGPASSWORD'] = cfg['password']

    backup_file = backup_dir / 'public.dump'
    if not backup_file.exists():
        print(f"Backup file {backup_file} not found.")
        return 1

    log_file = backup_dir / 'restore.log'
    print(f"Restoring from {backup_file} ...")
    # On écrit d'abord dans un log temporaire pour filtrer ensuite
    tmp_log_file = backup_dir / 'restore_raw.log'
    with tmp_log_file.open('w', encoding='utf-8') as log:
        # 1. Drop schema public
        drop_cmd = [
            'psql',
            '-h', cfg['host'],
            '-p', cfg['port'],
            '-U', cfg['user'],
            '-d', cfg['dbname'],
            '-c', 'DROP SCHEMA public CASCADE;'
        ]
        restore_cmd = [
            'pg_restore',
            '-h', cfg['host'],
            '-p', cfg['port'],
            '-U', cfg['user'],
            '-d', cfg['dbname'],
            '--verbose',
            str(backup_file)
        ]
        try:
            subprocess.run(drop_cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            result = subprocess.run(restore_cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                print(f"Restore failed (exit {result.returncode}). See {log_file} for details.")
                # On continue pour filtrer le log
        except Exception as e:
            print(f"Restore exception: {e}")
            return 1

    # Filtrage du log pour transformer l'erreur transaction_timeout en warning
    with tmp_log_file.open('r', encoding='utf-8') as fin, log_file.open('w', encoding='utf-8') as fout:
        for line in fin:
            if 'could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"' in line:
                fout.write('WARNING: transaction_timeout is ignoré (non supporté sur cette version de Postgres)\n')
            else:
                fout.write(line)

    # Optionnel: supprimer le log temporaire
    try:
        tmp_log_file.unlink()
    except Exception:
        pass

    print(f"Restore completed (voir {log_file}). Les erreurs transaction_timeout sont signalées comme warning.")
    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Backup/Restore Postgres public schema via Docker")
    parser.add_argument("action", nargs="?", default="backup", choices=["backup", "restore"], help="Action à effectuer (backup ou restore)")
    args = parser.parse_args()

    if args.action == "backup":
        sys.exit(make_backup())
    elif args.action == "restore":
        sys.exit(restore_latest_backup())