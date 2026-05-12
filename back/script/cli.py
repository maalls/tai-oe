import argparse
import os
import sys
import ssl
import csv
import io
import re
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install PyYAML")
    sys.exit(1)

# Prefer psycopg2 if available; else fall back to pg8000 (pure Python)
_pg_driver = None
try:
    import psycopg2  # type: ignore
    _pg_driver = "psycopg2"
except Exception:
    try:
        import pg8000  # type: ignore
        _pg_driver = "pg8000"
    except Exception:
        print("Missing DB driver. Install one of: psycopg2-binary or pg8000")
        sys.exit(1)


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        print(f"Config file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_schema(conn, schema_path: str):
    if not os.path.isabs(schema_path):
        # Resolve relative to repo root (this script is in back/script)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        schema_path = os.path.join(repo_root, schema_path)
    if not os.path.exists(schema_path):
        print(f"Schema file not found: {schema_path}")
        sys.exit(1)
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    cur = conn.cursor()
    cur.execute(sql)
    try:
        cur.close()
    except Exception:
        pass
    try:
        conn.commit()
    except Exception:
        pass
    print("Schema applied successfully.")


def database_create(config_path: str):
    cfg = load_config(config_path)
    supa = cfg.get("supabase", {})
    db = supa.get("db", {})
    schema_file = supa.get("schema_file", "back/schema/schema.sql")

    required = ["host", "port", "database", "user", "password"]
    missing = [k for k in required if not db.get(k)]
    if missing:
        print(f"Missing DB config keys: {', '.join(missing)} in {config_path}")
        sys.exit(1)

    conn = _create_db_and_connect(db)

    try:
        apply_schema(conn, schema_file)
    finally:
        conn.close()


def _create_db_and_connect(db: dict):
    """Create database if needed and return connection to it."""
    target_db = db.get("database")
    db_for_creation = db.copy()
    db_for_creation["database"] = "postgres"
    
    try:
        conn_postgres = _connect(db_for_creation)
        conn_postgres.autocommit = True
        cur = conn_postgres.cursor()
        
        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (target_db,)
        )
        exists = cur.fetchone() is not None
        
        if not exists:
            print(f"Creating database '{target_db}'...")
            cur.execute(f'CREATE DATABASE "{target_db}"')
            print(f"Database '{target_db}' created successfully.")
        else:
            print(f"Database '{target_db}' already exists.")
        
        cur.close()
        conn_postgres.close()
    except Exception as e:
        print(f"Failed to create database: {e}")
        sys.exit(1)

    # Now connect to the target database
    try:
        return _connect(db)
    except Exception as e:
        print(f"Failed to connect to Postgres: {e}")
        sys.exit(1)


def _connect(db: dict):
        host = db.get("host")
        port = int(db.get("port", 5432))
        database = db.get("database")
        user = db.get("user")
        password = db.get("password")
        sslmode = db.get("sslmode", "prefer")

        if _pg_driver == "psycopg2":
            dsn = (
                f"host={host} port={port} dbname={database} "
                f"user={user} password={password} sslmode={sslmode}"
            )
            import psycopg2  # type: ignore
            return psycopg2.connect(dsn)
        else:
            import pg8000  # type: ignore
            kwargs = {
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password,
            }
            if sslmode in ("require", "verify-ca", "verify-full"):
                kwargs["ssl_context"] = ssl.create_default_context()
            return pg8000.connect(**kwargs)


def _detect_delimiter(line: str) -> str:
    for candidate in (";", ",", "\t", "|"):
        if candidate in line:
            return candidate
    return ","


def _normalize_fabdis_header(content: str) -> str:
    return re.sub(
        r"LIBELLE240\r?\n,?DATETARIF",
        "LIBELLE240,DATETARIF",
        content,
        count=1,
    )


def _normalize_path(path: str) -> str:
    if not path:
        return path

    if not os.path.isabs(path):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate = os.path.join(repo_root, path)
        if os.path.exists(candidate):
            return candidate

    if not os.path.exists(path) and path.startswith("/malo/"):
        corrected = f"/Users{path}"
        if os.path.exists(corrected):
            return corrected

    return path


_CARTOUCHE_FILES = ("B00_CARTOUCHES.csv", "B00_CARTOUCHE.csv")


def _cartouche_csv_paths(data_dir: str) -> list[str]:
    return [os.path.join(data_dir, name) for name in _CARTOUCHE_FILES]


def _collect_fabdis_marques(data_dir: str, encoding: str) -> set[str]:
    marques: set[str] = set()
    cartouches_paths = _cartouche_csv_paths(data_dir)
    commerce_path = os.path.join(data_dir, "B01_COMMERCE.csv")

    for path, column in (
        *[(path, "CARMARQUE") for path in cartouches_paths],
        (commerce_path, "MARQUE"),
    ):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
            if content.startswith("\ufeff"):
                content = content[1:]
            content = _normalize_fabdis_header(content)
            lines = content.splitlines()
            sample_line = lines[0] if lines else ""
            delimiter = _detect_delimiter(sample_line)
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            for row in reader:
                raw_val = row.get(column, "")
                if isinstance(raw_val, str):
                    val = raw_val.strip()
                    if val:
                        marques.add(val)
    return marques


def _is_column_indexed(conn, table: str, column: str) -> bool:
    query = """
        SELECT 1
        FROM pg_index i
        JOIN pg_class t ON t.oid = i.indrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
        WHERE t.relname = %s AND a.attname = %s
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(query, (table, column))
        return cur.fetchone() is not None


def _clear_fabdis_rows(conn, marques_to_clear: set[str], check_indexes: bool = True) -> None:
    if not marques_to_clear:
        print("No marques found to clear; skipping delete step.")
        return

    default_batch_size = 1000
    table_batch_size = {
        "fabdis_article": 5000,
    }
    marques_list = list(marques_to_clear)

    table_marque_column = {
        "fabdis_cartouches": "carmarque",
        "fabdis_article": "marque",
        "fabdis_commerce": "marque",
        "fabdis_logistique": "marque",
        "fabdis_media": "marque",
        "fabdis_reglementaire": "marque",
        "fabdis_correspondance": "marque",
        "fabdis_variante": "marque",
        "fabdis_etim": "marque",
        "fabdis_extension": "marque",
        "fabdis_arret": "marqueass",
        "fabdis_substitution": "marquesub",
        "fabdis_pyramide": "marquep",
    }
    clear_order = [
        "fabdis_substitution",
        "fabdis_arret",
        "fabdis_extension",
        "fabdis_pyramide",
        "fabdis_etim",
        "fabdis_variante",
        "fabdis_correspondance",
        "fabdis_reglementaire",
        "fabdis_media",
        "fabdis_logistique",
        "fabdis_commerce",
        "fabdis_article",
        "fabdis_cartouches",
    ]

    print(f"Clearing FAB-DIS rows for marques: {', '.join(sorted(marques_to_clear))}")

    if check_indexes:
        for table in clear_order:
            column = table_marque_column.get(table)
            if not column:
                continue
            if not _is_column_indexed(conn, table, column):
                print(f"⚠ Missing index: {table}({column})")

    with conn.cursor() as cur:
        for table in clear_order:
            column = table_marque_column.get(table)
            if not column:
                continue

            cur.execute("SET LOCAL statement_timeout = %s", ("10s",))
            cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} = ANY(%s)",
                (marques_list,)
            )
            delete_count = cur.fetchone()[0]
            print(f"Deleting {delete_count} rows from {table} where {column} in target marques...")

            batch_size = table_batch_size.get(table, default_batch_size)
            while True:
                print(f"Deleting batch of up to {batch_size} rows from {table}...")
                cur.execute("SET LOCAL statement_timeout = %s", ("10s",))
                cur.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE ctid IN (
                        SELECT ctid
                        FROM {table}
                        WHERE {column} = ANY(%s)
                        LIMIT %s
                    )
                    """,
                    (marques_list, batch_size),
                )
                if cur.rowcount == 0:
                    break
            conn.commit()
    print("Existing data cleared for target marques.")


def database_sync_etim(config_path: str, etim_dir: str = None):
    """Load ETIM CSV data into database."""
    cfg = load_config(config_path)
    supa = cfg.get("supabase", {})
    db = supa.get("db", {})
    
    # Default ETIM directory
    if etim_dir is None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        etim_dir = os.path.join(repo_root, "back", "var", "storage")
        # Find ETIM directory (matches ETIM-* pattern)
        etim_candidates = [d for d in Path(etim_dir).glob("ETIM-*") if d.is_dir()]
        if not etim_candidates:
            print(f"No ETIM directory found in {etim_dir}")
            sys.exit(1)
        etim_dir = str(etim_candidates[0])
    
    print(f"Loading ETIM data from: {etim_dir}")
    
    _sync_csv_to_tables(db, etim_dir, _get_etim_mappings(), "ETIM")


def database_sync_fabdis(config_path: str, fabdis_dir: str = None):
    """Load FAB-DIS CSV data into database."""
    cfg = load_config(config_path)
    supa = cfg.get("supabase", {})
    db = supa.get("db", {})
    
    # Default FAB-DIS directory
    if fabdis_dir is None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fabdis_dir = os.path.join(repo_root, "back", "var", "storage")
        # Find FAB-DIS directory (matches FABDIS-* pattern)
        fabdis_candidates = [d for d in Path(fabdis_dir).glob("FABDIS-*") if d.is_dir()]
        if not fabdis_candidates:
            print(f"No FAB-DIS directory found in {fabdis_dir}")
            sys.exit(1)
        fabdis_dir = str(fabdis_candidates[0])
    
    fabdis_dir = _normalize_path(fabdis_dir) if fabdis_dir else fabdis_dir
    print(f"Loading FAB-DIS data from: {fabdis_dir}")
    mapping = _get_fabdis_mappings()
    _sync_csv_to_tables(db, fabdis_dir, mapping, "FAB-DIS")


def database_clear_fabdis(config_path: str, fabdis_dir: str = None, marques: str | None = None):
    """Clear FAB-DIS rows for target marques."""
    cfg = load_config(config_path)
    supa = cfg.get("supabase", {})
    db = supa.get("db", {})

    marques_to_clear: set[str] = set()
    if marques:
        marques_to_clear = {m.strip() for m in marques.split(",") if m.strip()}
    elif fabdis_dir:
        fabdis_dir = _normalize_path(fabdis_dir)
        marques_to_clear = _collect_fabdis_marques(fabdis_dir, "utf-8")
    else:
        print("Provide --marques or --fabdis-dir to determine target marques.")
        sys.exit(1)

    conn = _create_db_and_connect(db)
    try:
        _clear_fabdis_rows(conn, marques_to_clear, check_indexes=True)
    finally:
        conn.close()


def _get_etim_mappings():
    """Return ETIM CSV to table mappings."""
    # Mapping of CSV files to database tables
    # Format: (csv_file, table_name, [(csv_column, db_column), ...])
    return [
        ("ETIMUNIT.csv", "etim_unit", [("UNITOFMEASID", "unitofmeasid"), ("UNITDESC", "unitdesc")]),
        ("ETIMARTGROUP.csv", "etim_art_group", [("ARTGROUPID", "artgroupid"), ("GROUPDESC", "groupdesc")]),
        ("ETIMFEATURE.csv", "etim_feature", [("FEATUREID", "featureid"), ("FEATUREDESC", "featuredesc")]),
        ("ETIMVALUE.csv", "etim_value", [("VALUEID", "valueid"), ("VALUEDESC", "valuedesc")]),
        ("ETIMARTCLASS.csv", "etim_art_class", [
            ("ARTCLASSID", "artclassid"),
            ("ARTCLASSDESC", "artclassdesc"),
            ("ARTCLASSVERSION", "artclassversion"),
            ("ARTGROUPID", "artgroupid")
        ]),
        ("ETIMARTCLASSFEATUREMAP.csv", "etim_art_class_feature_map", [
            ("ARTCLASSFEATURENR", "artclassfeaturenr"),
            ("ARTCLASSID", "artclassid"),
            ("FEATUREID", "featureid"),
            ("FEATURETYPE", "featuretype"),
            ("UNITOFMEASID", "unitofmeasid"),
            ("SORTNR", "sortnr"),
        ]),
        ("ETIMARTCLASSFEATUREVALUEMAP.csv", "etim_art_class_feature_value_map", [
            ("ARTCLASSFEATUREVALUENR", "artclassfeaturevaluenr"),
            ("ARTCLASSFEATURENR", "artclassfeaturenr"),
            ("VALUEID", "valueid"),
        ]),
        ("ETIMARTCLASSSYNONYMMAP.csv", "etim_art_class_synonym", [
            ("ARTCLASSID", "artclassid"),
            ("CLASSSYNONYM", "classsynonym")
        ]),
    ]


def _get_fabdis_mappings():
    """Return FAB-DIS CSV to table mappings."""
    # Note: CSV columns are uppercase, DB columns are lowercase
    return [
        ("B00_CARTOUCHES.csv", "fabdis_cartouches", [
            ("NSCRIPT", "nscript"), ("CARTYP", "cartyp"), ("DATEDIT", "datedit"), ("DATEAPPLI", "dateappli"),
            ("DEFT", "deft"), ("DEV", "dev"), ("CARINFO", "carinfo"), ("CARINFOURLT", "carinfourlt"),
            ("NRB01", "nrb01"), ("NRC05", "nrc05"), ("FABDISV", "fabdisv"), ("LANG", "lang"),
            ("DECSEP", "decsep"), ("GROUPE", "groupe"), ("FABRICANT", "fabricant"), ("CARMARQUE", "carmarque"),
            ("CARMARQUEURLT", "carmarqueurlt"), ("CARNOM", "carnom"), ("CARPRENOM", "carprenom"),
            ("CAREMAIL", "caremail"), ("LEGAL", "legal"), ("LEGALURLT", "legalurlt")
        ]),
        ("B01_COMMERCE.csv", "fabdis_commerce", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("CTYP", "ctyp"), ("GTIN", "gtin"),
            ("REFINFOR", "refinfor"), ("GAMME", "gamme"), ("FONCTION", "fonction"), ("LIBELLE40", "libelle40"),
            ("LIBELLE80", "libelle80"), ("LIBELLE240", "libelle240"), ("DATETARIF", "datetarif"),
            ("TARIF", "tarif"), ("TARIFD", "tarifd"), ("QT", "qt"), ("TVA", "tva"), ("UB", "ub"),
            ("QMC", "qmc"), ("MUL", "mul"), ("QMV", "qmv"), ("QMVT", "qmvt"), ("QPKI", "qpki"),
            ("UC", "uc"), ("UCCOEF", "uccoef"), ("ST", "st"), ("DELAI", "delai"), ("EDI", "edi"),
            ("DUG", "dug"), ("STA", "sta"), ("DATEPREV", "dateprev"), ("DOUANE", "douane"),
            ("MKT1", "mkt1"), ("MKT1L", "mkt1l"), ("MKT2", "mkt2"), ("MKT2L", "mkt2l"),
            ("MKT3", "mkt3"), ("MKT3L", "mkt3l"), ("MKT4", "mkt4"), ("MKT4L", "mkt4l"),
            ("MKT5", "mkt5"), ("MKT5L", "mkt5l"), ("FAM1", "fam1"), ("FAM1L", "fam1l"),
            ("FAM2", "fam2"), ("FAM2L", "fam2l"), ("FAM3", "fam3"), ("FAM3L", "fam3l")
        ]),
        ("B02_LOGISTIQUE.csv", "fabdis_logistique", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("LTYP", "ltyp"), ("LCODE", "lcode"),
            ("LQTE", "lqte"), ("LNUM", "lnum"), ("QC", "qc"), ("QCT", "qct"), ("LGTIN", "lgtin"),
            ("HAUT", "haut"), ("HAUTU", "hautu"), ("LARG", "larg"), ("LARGU", "largu"),
            ("PROF", "prof"), ("PROFU", "profu"), ("POIDS", "poids"), ("POIDSU", "poidsu"),
            ("VOL", "vol"), ("VOLU", "volu"), ("DIAM", "diam"), ("DIAMU", "diamu"),
            ("SECT", "sect"), ("SECTU", "sectu"), ("LINFO", "linfo")
        ]),
        ("B03_MEDIA.csv", "fabdis_media", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("MTYP", "mtyp"), ("MCIB", "mcib"),
            ("MNUM", "mnum"), ("MCODE", "mcode"), ("MLANG", "mlang"), ("MINFO", "minfo"),
            ("MVAL", "mval"), ("MVU", "mvu"), ("MTEXTE", "mtexte"), ("MNOM", "mnom"),
            ("MURL", "murl"), ("MURLT", "murlt")
        ]),
        ("B04_REGLEMENTAIRE.csv", "fabdis_reglementaire", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("RTYP", "rtyp"), ("RFLAG", "rflag"),
            ("RNUM", "rnum"), ("RCODE1", "rcode1"), ("RCODE2", "rcode2"), ("RCODE3", "rcode3"),
            ("RQTE", "rqte"), ("RPCT", "rpct"), ("RDATE", "rdate"), ("RVAL", "rval"),
            ("RVU", "rvu"), ("RTEXTE", "rtexte"), ("RNOM", "rnom"), ("RURL", "rurl"), ("RURLT", "rurlt")
        ]),
        ("C02_CORRESPONDANCE.csv", "fabdis_correspondance", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("CORTYP", "cortyp"), ("CORNUM", "cornum"),
            ("CORQ", "corq"), ("REFCIALECOR", "refciale_cor"), ("MARQUECOR", "marque_cor"),
            ("CORLOT", "corlot"), ("COROUE", "coroue"), ("CORINFO", "corinfo")
        ]),
        ("C03_VARIANTE.csv", "fabdis_variante", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("VCODE", "vcode"), ("VCODELIBELLE", "vcodelibelle"),
            ("VTYP", "vtyp"), ("VARIANTE", "variante"), ("VFABDIS", "vfabdis"), ("VVALEUR", "vvaleur"),
            ("VUNITE", "vunite"), ("VNUMV", "vnumv"), ("VNUMR", "vnumr")
        ]),
        ("C04_ETIM.csv", "fabdis_etim", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("ARTCLASSID", "artclassid"),
            ("FEATUREID", "featureid"), ("FVALUE", "fvalue"), ("GROUPDESC", "groupdesc"),
            ("ARTCLASSDESC", "artclassdesc"), ("FEATUREDESC", "featuredesc"),
            ("VALUEDESC", "valuedesc"), ("UNITDESC", "unitdesc")
        ]),
        ("F01_PYRAMIDE.csv", "fabdis_pyramide", [
            ("NIV", "niv"), ("MKTC", "mktc"), ("MKT", "mkt"), ("MKTL", "mktl"),
            ("GAMMEP", "gammep"), ("MARQUEP", "marquep")
        ]),
        ("C01_EXTENSION.csv", "fabdis_extension", [
            ("MARQUE", "marque"), ("REFCIALE", "refciale"), ("ETYP", "etyp"), ("EFLAG", "eflag"),
            ("ENUM", "enum"), ("ECODE1", "ecode1"), ("ECODE2", "ecode2"), ("EQTE", "eqte"),
            ("EPCT", "epct"), ("EDATE", "edate"), ("EVAL1", "eval1"), ("EVU1", "evu1"),
            ("EVAL2", "eval2"), ("EVU2", "evu2"), ("ETEXTE", "etexte"), ("ENOM", "enom"),
            ("EURL", "eurl"), ("EURLT", "eurlt")
        ]),
        ("C05_ARRET.csv", "fabdis_arret", [
            ("MQEREFARRET", "mqerefarret"), ("REFARRET", "refarret"), ("ATYP", "atyp"),
            ("ADATE", "adate"), ("REFCIALEASS", "refcialeass"), ("MARQUEASS", "marqueass"),
            ("ACODE", "acode"), ("AQTE", "aqte"), ("AVAL", "aval"), ("AVU", "avu"),
            ("ATEXTE", "atexte"), ("ANOM", "anom"), ("AURL", "aurl"), ("AURLT", "aurlt")
        ]),
        ("C06_SUBSTITUTION.csv", "fabdis_substitution", [
            ("MQEREFOLD", "mqerefold"), ("REFOLD", "refold"), ("REFCIALESUB", "refcialesub"),
            ("MARQUESUB", "marquesub"), ("STYP", "styp"), ("SINFO", "sinfo"),
            ("SQD", "sqd"), ("SQB", "sqb"), ("SLOT", "slot"), ("SPCT", "spct")
        ]),
    ]


def _sync_csv_to_tables(db: dict, data_dir: str, mappings: list, dataset_name: str):
    data_dir = _normalize_path(data_dir)
    conn = _create_db_and_connect(db)
    
    # Determine if UTF-16LE (ETIM) or UTF-8 (FAB-DIS)
    encoding = 'utf-16-le' if dataset_name == "ETIM" else 'utf-8'
    delimiter = ';' if dataset_name == "ETIM" else ','
    print(f"Using encoding '{encoding}' and delimiter '{delimiter}' for {dataset_name} dataset.")
    
    try:
        cur = conn.cursor()
        print(f"Connected to database for {dataset_name} sync.")
        
        # Clear tables based on dataset
        if dataset_name == "ETIM":
            print("Clearing existing ETIM data...")
            clear_order = [
                "etim_art_class_synonym",
                "etim_art_class_feature_value_map",
                "etim_art_class_feature_map",
                "etim_art_class",
                "etim_value",
                "etim_feature",
                "etim_unit",
                "etim_art_group",
            ]
        else:  # FAB-DIS
            print("Clearing existing FAB-DIS data...")
            
            clear_order = [
                "fabdis_substitution",
                "fabdis_arret",
                "fabdis_extension",
                "fabdis_pyramide",
                "fabdis_etim",
                "fabdis_variante",
                "fabdis_correspondance",
                "fabdis_reglementaire",
                "fabdis_media",
                "fabdis_logistique",
                "fabdis_commerce",
                "fabdis_article",
                "fabdis_cartouches",
            ]
        
        if dataset_name == "FAB-DIS":
            marques_to_clear = _collect_fabdis_marques(data_dir, encoding)
            _clear_fabdis_rows(conn, marques_to_clear, check_indexes=True)
        else:
            for table in clear_order:
                cur.execute(f"DELETE FROM {table}")
            conn.commit()
            print("Existing data cleared.")
        
        # Load data
        cartouches_loaded = False
        cartouche_marques = set()
        
        for csv_file, table_name, columns in mappings:
            csv_path = os.path.join(data_dir, csv_file)
            if not os.path.exists(csv_path):
                if csv_file in _CARTOUCHE_FILES:
                    alt_path = next((p for p in _cartouche_csv_paths(data_dir) if os.path.exists(p)), None)
                    if alt_path:
                        csv_path = alt_path
                    else:
                        print(f"Warning: CSV file not found: {csv_path}")
                        continue
                else:
                    print(f"Warning: CSV file not found: {csv_path}")
                    continue
            
            print(f"Loading {csv_file} into {table_name}...")
            
            # Load CSV data
            with open(csv_path, 'r', encoding=encoding) as f:
                # Skip BOM if present (ETIM files)
                content = f.read()
                if content.startswith('\ufeff'):
                    content = content[1:]

                if dataset_name == "FAB-DIS":
                    content = _normalize_fabdis_header(content)

                lines = content.splitlines()
                sample_line = lines[0] if lines else ""
                effective_delimiter = (
                    _detect_delimiter(sample_line)
                    if dataset_name == "FAB-DIS"
                    else delimiter
                )

                reader = csv.DictReader(io.StringIO(content), delimiter=effective_delimiter)
                
                # Collect all rows for batch insert
                batch_rows = []
                db_columns = [db_col for csv_col, db_col in columns]
                
                # For B01_COMMERCE, also populate fabdis_article anchor table first
                if table_name == "fabdis_commerce":
                    print(f"  → Populating fabdis_article anchor table...")
                    article_rows = set()
                
                for row in reader:
                    # Extract values mapping CSV columns to DB columns
                    values = []
                    for csv_col, db_col in columns:
                        raw_val = row.get(csv_col, '')
                        if raw_val is None:
                            val = None
                        else:
                            val = raw_val.strip() if isinstance(raw_val, str) else str(raw_val).strip()
                            val = val or None
                        
                        # Convert DD/MM/YYYY dates to YYYY-MM-DD for FAB-DIS
                        if dataset_name == "FAB-DIS" and val and db_col.endswith(('date', 'datedit', 'dateappli', 'datetarif', 'dateprev', 'rdate', 'edate', 'adate')):
                            try:
                                # Try parsing DD/MM/YYYY format
                                if '/' in val:
                                    dt = datetime.strptime(val, '%d/%m/%Y')
                                    val = dt.strftime('%Y-%m-%d')
                            except ValueError:
                                pass  # Keep original if parsing fails
                        
                        # Sanitize numeric fields - set to NULL if not numeric
                        if dataset_name == "FAB-DIS" and val and db_col in (
                            'tarif', 'tarifd', 'qt', 'tva', 'qmc', 'mul', 'qmv', 'uccoef', 'delai',
                            'lqte', 'qc', 'qct', 'haut', 'larg', 'prof', 'poids', 'vol', 'diam', 'sect',
                            'rqte', 'rpct', 'rval', 'cornum', 'corq', 'vnumv', 'vnumr', 'eqte', 'epct',
                            'eval1', 'eval2', 'aqte', 'aval', 'sqd', 'sqb', 'spct', 'nrb01', 'nrc05'
                        ):
                            try:
                                # Try converting to float to verify it's numeric
                                float(val)
                            except (ValueError, TypeError):
                                val = None  # Set to NULL if not numeric
                        
                        values.append(val)
                    batch_rows.append(values)

                    if table_name == "fabdis_cartouches":
                        raw_carmarque = row.get("CARMARQUE", "")
                        if isinstance(raw_carmarque, str):
                            carmarque = raw_carmarque.strip()
                            if carmarque:
                                cartouche_marques.add(carmarque)
                    
                    # Collect unique (marque, refciale) pairs for article table
                    if table_name == "fabdis_commerce":
                        raw_marque = row.get('MARQUE', '')
                        raw_refciale = row.get('REFCIALE', '')
                        marque = raw_marque.strip() if isinstance(raw_marque, str) else None
                        refciale = raw_refciale.strip() if isinstance(raw_refciale, str) else None
                        if marque and refciale:
                            article_rows.add((marque, refciale))
                
                if table_name == "fabdis_cartouches":
                    cartouches_loaded = True

                # Insert articles first if needed
                if table_name == "fabdis_commerce" and article_rows:
                    if not cartouches_loaded:
                        marque_rows = sorted({pair[0] for pair in article_rows if pair[0]})
                        if marque_rows:
                            cur.executemany(
                                "INSERT INTO fabdis_cartouches (carmarque) VALUES (%s) ON CONFLICT (carmarque) DO NOTHING",
                                [(marque,) for marque in marque_rows]
                            )
                            conn.commit()
                            cartouche_marques.update(marque_rows)
                            cartouches_loaded = True
                            print(f"  → {len(marque_rows)} cartouches inserted for missing B00_CARTOUCHES")
                        else:
                            print("  ⚠ Skipping fabdis_article insert (no marques found)")

                    if cartouche_marques:
                        article_rows = {pair for pair in article_rows if pair[0] in cartouche_marques}
                    if article_rows:
                        cur.executemany(
                            "INSERT INTO fabdis_article (marque, refciale) VALUES (%s, %s)",
                            list(article_rows)
                        )
                        conn.commit()
                        print(f"  → {len(article_rows)} articles inserted into fabdis_article")
                    else:
                        print("  ⚠ No matching cartouches for fabdis_article insert")
                
                # Batch insert all rows at once
                if batch_rows:
                    placeholders = ', '.join(['%s'] * len(db_columns))
                    cols = ', '.join(db_columns)
                    conflict_clause = ""
                    if table_name == "fabdis_arret":
                        update_cols = [col for col in db_columns if col != "refarret"]
                        if update_cols:
                            set_clause = ", ".join(
                                f"{col} = EXCLUDED.{col}" for col in update_cols
                            )
                            conflict_clause = f" ON CONFLICT (refarret) DO UPDATE SET {set_clause}"
                        else:
                            conflict_clause = " ON CONFLICT (refarret) DO NOTHING"
                    insert_sql = (
                        f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}){conflict_clause}"
                    )
                    batch_size = 5000
                    
                    try:
                        # Insert in chunks to avoid massive single executemany calls.
                        for start in range(0, len(batch_rows), batch_size):
                            print(f"  → Inserting batch {start // batch_size + 1} ({min(batch_size, len(batch_rows) - start)} rows)...")
                            chunk = batch_rows[start:start + batch_size]
                            cur.executemany(insert_sql, chunk)
                        rows_inserted = len(batch_rows)
                    except Exception as e:
                        print(f"Error inserting batch into {table_name}: {e}")
                        raise
                
                conn.commit()
                print(f"  → {rows_inserted} rows inserted")
        
        cur.close()
        print(f"{dataset_name} data sync completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during {dataset_name} sync: {e}")
        sys.exit(1)
    finally:
        conn.close()



def main():
    parser = argparse.ArgumentParser(prog="cli", description="Project administration CLI")
    parser.add_argument("command", help="Command to run, e.g. database:create, database:sync:etim, database:sync:fabdis")
    parser.add_argument("--config", dest="config", default=os.path.join(os.path.dirname(__file__), "..", "config.yml"),
                        help="Path to config.yml")
    parser.add_argument("--etim-dir", dest="etim_dir", default=None,
                        help="Path to ETIM CSV directory (default: auto-detect in var/storage/)")
    parser.add_argument("--fabdis-dir", dest="fabdis_dir", default=None,
                        help="Path to FAB-DIS CSV directory (default: auto-detect in var/storage/)")
    parser.add_argument("--marques", dest="marques", default=None,
                        help="Comma-separated list of FAB-DIS marques to clear")
    args = parser.parse_args()

    if args.command == "database:create":
        database_create(args.config)
    elif args.command == "database:sync:etim":
        database_sync_etim(args.config, args.etim_dir)
    elif args.command == "database:sync:fabdis":
        database_sync_fabdis(args.config, args.fabdis_dir)
    elif args.command == "database:clear:fabdis":
        database_clear_fabdis(args.config, args.fabdis_dir, args.marques)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
