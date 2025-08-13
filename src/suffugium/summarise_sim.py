import duckdb
import csv
import pathlib as pl


class SimSummerizer(object):
    '''This class is in charge of post simulation summarization and csv cleanup.'''
    def __init__(self, model, db_path=None):
        self.model = model
        self.csv_folder = self.model.output_folder
        self.table_name = "SimSummary"
        if db_path:
            db_path = pl.Path(db_path).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Using persistent DuckDB at {db_path}")
            self.con = duckdb.connect(str(db_path))
        else:
            print(f"[INFO] Using in-memory DuckDB database")
            self.con = duckdb.connect(database=":memory:")

    def create_table(self):
        self.con.execute(f"""
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
            Metabolic_state DOUBLE,
            Prey_Density DOUBLE,
            Attack_Rate DOUBLE,
            Prey_Consumed INTEGER,
            Cause_of_Death TEXT
        );

        """)
        return

    def insert_csv(self, csv_path, site, experiment):
        self.con.execute(f"""
                INSERT INTO {self.table_name}
                SELECT
                    Time_Step,
                    Hour, 
                    Day, 
                    Month, 
                    Year, 
                    Site_Name,
                    Rattlesnakes, 
                    Krats, 
                    Rattlesnakes_Density, 
                    Krats_Density, 
                    Rattlesnakes_Active, 
                    Krats_Active,
                    Foraging, 
                    Thermoregulating, 
                    Resting, 
                    Searching, 
                    Brumating,
                    Snakes_in_Burrow, 
                    Snakes_in_Open,
                    mean_thermal_quality, 
                    mean_thermal_accuracy, 
                    mean_metabolic_state,
                    count_interactions, 
                    count_successful_interactions,
                    seed, 
                    sim_id
                FROM read_csv_auto('{csv_path}')
            """)
        return