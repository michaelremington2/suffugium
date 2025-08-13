import duckdb
import csv
import pathlib as pl


class SimSummerizer(object):
    '''This class is in charge of post simulation summarization and csv cleanup.'''
    def __init__(self, model, db_path=None):
        self.model = model
        if db_path:
            db_path = pl.Path(db_path).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Using persistent DuckDB at {db_path}")
            self.con = duckdb.connect(str(db_path))
        else:
            print(f"[INFO] Using in-memory DuckDB database")
            self.con = duckdb.connect(database=":memory:")