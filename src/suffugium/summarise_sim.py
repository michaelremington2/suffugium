import duckdb
import csv
import pathlib as pl
import os
import time
import random
from typing import Callable, Any, Tuple, Dict


LOCK_MSG_SNIPPETS = (
    "Could not set lock on file",     # common DuckDB lock message
    "database is locked",             # generic wording, just in case
    "IO Error: Could not set lock",   # variant
)

class SimSummerizer(object):
    '''This class is in charge of post simulation summarization and csv cleanup.'''

    def __init__(self, table_name, csv_folder, db_path=None, read_only=False,
                 max_retries: int = 30, min_wait: int = 60, max_wait: int = 120):
        self.csv_folder = csv_folder
        self.table_name = table_name
        self.read_only = bool(read_only)
        self.max_retries = max_retries
        self.min_wait = min_wait
        self.max_wait = max_wait

        if db_path:
            db_path = pl.Path(db_path).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            mode = "READ ONLY" if self.read_only else "READ/WRITE"
            print(f"[INFO] Using persistent DuckDB at {db_path} ({mode})")

            # Use retry around connect (most likely place to hit the lock)
            def _do_connect():
                # DuckDB Python supports read_only=... flag
                return duckdb.connect(str(db_path), read_only=self.read_only)

            self.con = self._retry(_do_connect, retry_on=duckdb.IOException)
        else:
            print(f"[INFO] Using in-memory DuckDB database")
            self.con = duckdb.connect(database=":memory:")

    # ------------- Retry helpers -------------

    def _should_retry_exc(self, exc: Exception) -> bool:
        msg = str(exc)
        return any(snip in msg for snip in LOCK_MSG_SNIPPETS)

    def _retry(self,
               func: Callable,
               *args,
               retry_on: Tuple[type, ...] = (Exception,),
               **kwargs) -> Any:
        """
        Retry a callable when we hit a DuckDB lock. Wait 60–120s between tries.
        """
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except retry_on as e:
                attempt += 1
                if not self._should_retry_exc(e) or attempt > self.max_retries:
                    # Not a lock error or we've exhausted retries
                    raise
                wait_s = random.randint(self.min_wait, self.max_wait)
                print(f"[WARN] DB appears locked (attempt {attempt}/{self.max_retries}). "
                      f"Sleeping {wait_s}s then retrying…\n       Error: {e}")
                time.sleep(wait_s)

    def execute_with_retry(self, sql: str):
        """Execute SQL with lock-aware retry; returns DuckDB cursor."""
        return self._retry(self.con.execute, sql, retry_on=(duckdb.IOException,))


    def create_table(self):
        self.execute_with_retry(f"""
        CREATE OR REPLACE TABLE {self.table_name} (
            Step_id INTEGER,
            Agent_ID INTEGER,
            Experiment_Name TEXT,
            Study_site TEXT,
            Experiment TEXT,
            Hour INTEGER,
            Day INTEGER,
            Month INTEGER,
            Season TEXT,
            Year INTEGER,
            Alive BOOLEAN,
            Active BOOLEAN,
            Mass DOUBLE,
            Behavior TEXT,
            Microhabitat TEXT,
            Body_Temperature DOUBLE,
            T_env DOUBLE,
            Thermal_Accuracy DOUBLE,
            Thermal_Quality DOUBLE,
            Metabolic_state DOUBLE,
            Prey_Density DOUBLE,
            Attack_Rate DOUBLE,
            Prey_Consumed INTEGER,
            Cause_of_Death TEXT,
            Sim_id INTEGER,
            config_file_name TEXT
        );
        """)
        return

    def insert_csv(self, csv_path):
        self.execute_with_retry(f"""
            INSERT INTO {self.table_name}
            SELECT
                Step_id,
                Agent_ID,
                Experiment_Name,
                Study_site,
                Experiment,
                Hour,
                Day,
                Month,
                Season,
                Year,
                Alive,
                Active,
                Mass,
                Behavior,
                Microhabitat,
                Body_Temperature,
                T_env,
                Thermal_Accuracy,
                Thermal_Quality,
                Metabolic_state,
                Prey_Density,
                Attack_Rate,
                Prey_Consumed,
                Cause_of_Death,
                Sim_id,
                config_file_name
            FROM read_csv_auto('{csv_path}')
        """)
        return

    def insert_all(self, csv_list):
        for file in csv_list:
            try:
                self.insert_csv(str(file))
            except Exception as e:
                print(f"[WARN] Failed to process {file}: {e}")
        return

    def query_model_table(self, query):
        """
        Execute a query on the model table and return the results as a DataFrame.
        """
        return self.execute_with_retry(query).fetchdf()

    def make_summary_df(self):
        summary_query = f"""
            SELECT
                s.Experiment_Name,
                s.Study_site,
                s.Agent_ID,
                s.Sim_id,
                s.config_file_name,
                MAX(s.Mass) AS Mass,
                MAX(s.Step_id) AS Last_Step,
                CASE WHEN MIN(s.Alive) = 1 THEN 'Alive' ELSE 'Dead' END AS Status,
                AVG(s.Body_Temperature) AS Average_Body_Temperature,
                AVG(s.T_env) AS Average_Environmental_Temperature,
                AVG(s.Thermal_Accuracy) AS Average_Thermal_Accuracy,
                AVG(s.Thermal_Quality) AS Average_Thermal_Quality,
                MAX(s.Prey_Density) AS Prey_Density,
                MAX(s.Attack_Rate) AS Attack_Rate,
                SUM(s.Prey_Consumed) AS Total_Prey_Consumed,
                AVG(s.Metabolic_state) AS Average_Metabolic_State,
                MAX(s.Cause_of_Death) AS Cause_of_Death,
                bc.Forage,
                bc.Rest,
                bc.Thermoregulate,
                bc.Brumate,
                bc.Search
            FROM {self.table_name} AS s
            LEFT JOIN (
                SELECT
                    Agent_ID,
                    SUM(CASE WHEN Behavior = 'Forage' THEN 1 ELSE 0 END) AS Forage,
                    SUM(CASE WHEN Behavior = 'Rest' THEN 1 ELSE 0 END) AS Rest,
                    SUM(CASE WHEN Behavior = 'Thermoregulate' THEN 1 ELSE 0 END) AS Thermoregulate,
                    SUM(CASE WHEN Behavior = 'Brumation' THEN 1 ELSE 0 END) AS Brumate,
                    SUM(CASE WHEN Behavior = 'Search' THEN 1 ELSE 0 END) AS Search
                FROM {self.table_name}
                GROUP BY Agent_ID
            ) AS bc ON s.Agent_ID = bc.Agent_ID
            GROUP BY
                s.Experiment_Name,
                s.Study_site,
                s.Agent_ID,
                s.Sim_id,
                s.config_file_name,
                bc.Forage,
                bc.Rest,
                bc.Thermoregulate,
                bc.Brumate,
                bc.Search;
        """
        return self.query_model_table(summary_query)

    def make_summary_csv(self, output_path):
        summary_df = self.make_summary_df()
        summary_df.to_csv(output_path, index=False)
        print(f"[INFO] Summary CSV created at {output_path}")
        return summary_df


if __name__ == "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results/')
    db_path = os.path.join(output_directory, 'suffugium.db')

    # If you’re only reading/aggregating, prefer read_only=True to avoid writer lock contention.
    simsum = SimSummerizer(
        table_name="Model",                # ← set this to your table name
        csv_folder=output_directory,
        db_path=db_path,
        read_only=True,                   # set False if you need to INSERT/CREATE
        max_retries=30,                   # ~30 attempts
        min_wait=60, max_wait=120         # wait 60–120s between attempts
    )

    csv_model_summary = os.path.join(output_directory, 'model_summary.csv')

    # Example writer flow (uncomment when you actually need to write):
    # simsum.create_table()
    # csv_files = pl.Path(output_directory).glob('*.csv')
    # simsum.insert_all(csv_files)

    print("All CSV files have been processed and inserted into the DuckDB table.")
    simsum.make_summary_csv(output_path=csv_model_summary)
