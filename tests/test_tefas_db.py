# tests/test_tefas_db.py
import os
from pathlib import Path
import pandas as pd

from finance_tools.config import get_config
from finance_tools.etfs.tefas.service import TefasPersistenceService


def _run_flow(db_path: Path):
    cfg = get_config()

    # Determine db file path; accept either directory or file path
    db_root = Path(db_path)
    if db_root.suffix == ".db" or db_root.is_file():
        db_file = db_root
    else:
        db_root.mkdir(parents=True, exist_ok=True)
        db_file = db_root / "test_finance_tools.db"

    # Ensure parent directory exists
    db_file.parent.mkdir(parents=True, exist_ok=True)

    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["DATABASE_NAME"] = str(db_file)
    cfg.reload()

    service = TefasPersistenceService()

    df = service.download_last_week()
    print("Number of rows in the dataframe:", 0 if df is None else df.shape[0])

    inserted_info, inserted_breakdown = service.persist_dataframe(df)
    print(f"Inserted/updated info rows: {inserted_info}")
    print(f"Inserted/updated breakdown rows: {inserted_breakdown}")

    rows = service.query_info("NNF")
    print("NNF sample rows:", rows[:5])

    return inserted_info, inserted_breakdown, rows


def test_download_and_persist_and_query_nnf(tmp_path):
    inserted_info, inserted_breakdown, rows = _run_flow(tmp_path)
    assert inserted_info >= 0
    assert inserted_breakdown >= 0
    assert isinstance(rows, list)
    if rows:
        assert rows[0]["code"] == "NNF"


if __name__ == "__main__":
    # Execute using a local temporary directory under CWD
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        _run_flow(Path(td))