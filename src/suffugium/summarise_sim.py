import duckdb
import csv
import pathlib as pl
import os


class SimSummerizer(object):
    '''This class is in charge of post simulation summarization and csv cleanup.'''
    def __init__(self, table_name, csv_folder, db_path=None):
        self.csv_folder = csv_folder
        self.table_name = table_name
        if db_path:
            db_path = pl.Path(db_path).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Using persistent DuckDB at {db_path}")
            self.con = duckdb.connect(str(db_path))
        else:
            print(f"[INFO] Using in-memory DuckDB database")
            self.con = duckdb.connect(database=":memory:")

    def create_table(self):
        # Step_id,Agent_ID,Experiment_Name,Study_site,Experiment,Hour,Day,Month,Season,Year,Alive,Active,Mass,Behavior,Microhabitat,Body_Temperature,T_env,Thermal_Accuracy,Thermal_Quality,Metabolic_state,Prey_Density,Attack_Rate,Prey_Consumed,Cause_of_Death
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
            Thermal_Accuracy DOUBLE,
            Thermal_Quality DOUBLE,
            Metabolic_state DOUBLE,
            Prey_Density DOUBLE,
            Attack_Rate DOUBLE,
            Prey_Consumed INTEGER,
            Cause_of_Death TEXT
        );

        """)
        return

    def insert_csv(self, csv_path):
        self.con.execute(f"""
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
                    Cause_of_Death
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
        return self.con.execute(query).fetchdf()
    
    def make_summary_df(self):
        """
        Create a summary of the simulation results.
        This method can be extended to perform more complex summarization tasks.
        """
        summary_query = f"""
            SELECT
                s.Experiment_Name,
                s.Study_site,
                s.Agent_ID,
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
                MAX(s.Cause_of_Death) AS Cause_of_Death
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
                bc.Forage,
                bc.Rest,
                bc.Thermoregulate,
                bc.Brumate,
                bc.Search;
            """
        return self.query_model_table(summary_query)
    
    def make_summary_csv(self, output_path):
        """
        Create a summary CSV file of the simulation results.
        """
        summary_df = self.make_summary_df()
        summary_df.to_csv(output_path, index=False)
        print(f"[INFO] Summary CSV created at {output_path}")
        return summary_df
    
if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results/')
    db_path = os.path.join(output_directory, 'suffugium.db')
    simsum  = SimSummerizer(csv_folder=output_directory, db_path=db_path)
    csv_model_summary = output_directory + 'model_summary.csv'
    # simsum.create_table()
    # csv_files = pl.Path(output_directory).glob('*.csv')
    # simsum.insert_all(csv_files)
    print("All CSV files have been processed and inserted into the DuckDB table.")
    simsum.make_summary_csv(output_path=csv_model_summary)  # Example query

