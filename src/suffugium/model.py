import numpy as np
import mesa
import yaml
import os
from suffugium.config_schema import RootConfig
import polars as po
import pathlib as pl
from suffugium.organism import Rattlesnake
from suffugium.summarise_sim import SimSummerizer
import time
import random

class Suffugium(mesa.Model):
    '''A model for simulating the survival of ectotherms at a given location.'''
    def __init__(self, sim_id, config, output_directory,db_path, seed=None, keep_data=0):
        super().__init__(seed=seed)
        self.sim_id = sim_id
        with open(config, "r") as f:
            _config = yaml.safe_load(f)
        self.config = RootConfig.model_validate(_config)
        self.study_site = self.config.Model_Parameters.Site
        self.experiment = self.config.Model_Parameters.Experiment
        self.keep_data = keep_data
        self.db_path = db_path
        self.experiment_name = f"{self.study_site}_{self.experiment}"
        if output_directory is not None:
            os.makedirs(output_directory, exist_ok=True)
            csvs_fp = os.path.join(output_directory, f'{self.experiment_name}_{self.sim_id}')
            self.output_directory = output_directory
            self.temp_csvs_fp = csvs_fp
            os.makedirs(self.temp_csvs_fp, exist_ok=True)
        else:
            self.output_directory = ''
        self.microhabitats = ['Burrow', 'Open']
        self.thermal_profile = po.read_csv(self.config.Landscape_Parameters.Thermal_Database_fp)
        self.env_columns = self.config.Landscape_Parameters.ENV_Temperature_Cols
        self.snake_population_size = self.config.Model_Parameters.agents.Rattlesnake
        self.open_temp_vector = self.thermal_profile.select(self.env_columns.Open)
        self.burrow_temp_vector = self.thermal_profile.select(self.env_columns.Burrow)
        self.step_id = 0
        self._burrow_temperature = None
        self._open_temperature = None
        self._hour = 0
        self._day = 0
        self._month = 0
        self._year = 0
        self.set_time()
        self.initialize_population()
        

    #####################################################################################
    ##
    ## Properties
    ##
    #####################################################################################

    @property
    def burrow_temperature(self):
        return self._burrow_temperature
    
    @burrow_temperature.setter
    def burrow_temperature(self, value):
        self._burrow_temperature = value
    
    @property
    def open_temperature(self):
        return self._open_temperature
    
    @open_temperature.setter
    def open_temperature(self, value):
        self._open_temperature = value

    @property
    def hour(self):
        return self._hour

    @hour.setter
    def hour(self, value):
        self._hour = value

    @property
    def day(self):
        return self._day

    @day.setter
    def day(self, value):
        self._day = value

    @property
    def month(self):
        return self._month

    @month.setter
    def month(self, value):
        self._month = value

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        self._year = value
    
    ######################################################################################
    ##
    ## Methods
    ##
    ######################################################################################
    
    def set_temperatures(self):
        # set these to env_cols
        open_temp = self.open_temp_vector.row(self.step_id)[0]
        burrow_temp = self.burrow_temp_vector.row(self.step_id)[0]
        self.open_temperature = open_temp
        self.burrow_temperature = burrow_temp

    def set_time(self):
        """Set the current time in the model."""
        self.hour = self.thermal_profile.select("hour").row(self.step_id)[0]
        self.day = self.thermal_profile.select('day').row(self.step_id)[0]
        self.month = self.thermal_profile.select('month').row(self.step_id)[0]
        self.year = self.thermal_profile.select('year').row(self.step_id)[0]

    def get_season(self):
        """Determine the season based on the month."""
        if self.month in [12, 1, 2]:
            return 'Winter'
        elif self.month in [3, 4, 5]:
            return 'Spring'
        elif self.month in [6, 7, 8]:
            return 'Summer'
        elif self.month in [9, 10, 11]:
            return 'Fall'
        else:
            raise ValueError(f"Invalid month: {self.month}")
    
    def get_timestamp(self):
        """Get the current timestamp as a string."""
        return f"{self.year}-{self.month:02d}-{self.day:02d} {self.hour:02d}:00:00"

    def get_temperature(self, microhabitat):
        if microhabitat == 'Burrow':
            return self.burrow_temperature
        elif microhabitat == 'Open':
            return self.open_temperature
        else:
            raise ValueError(f"Unknown microhabitat: {microhabitat}")

    def initialize_population(self):
        Rattlesnake.create_agents(model=self, 
                                  n=self.snake_population_size,
                                  config=self.config.Rattlesnake_Parameters,
                                  interaction_config=self.config.Interaction_Parameters)
        
    def remove_agent(self, agent):
        """Remove an agent from the model."""
        self.agents.remove(agent)  # Removes from scheduler/AgentSet

    def summarize_simulation(self):
        """
        Summarize the simulation results and store them in a database.
        """
        simsum = SimSummerizer(table_name=self.experiment_name, csv_folder=self.temp_csvs_fp, db_path=self.db_path)
        csv_files = pl.Path(self.temp_csvs_fp).glob('*.csv')
        simsum.create_table()
        simsum.insert_all(csv_files)
        simsum.make_summary_csv(os.path.join(self.output_directory, f'{self.experiment_name}_model_summary.csv'))
        print("[INFO] Simulation summary completed.")
        # clean up temporary CSV files if keep_data is not set
        csv_files = pl.Path(self.temp_csvs_fp).glob('*.csv')
        keep_data_counter = self.keep_data
        for i, file in enumerate(csv_files):
            if i < keep_data_counter:
                continue  # keep it
            print(f"[INFO] Removing temporary file: {file}")
            os.remove(file)  # remove it
        print("[INFO] All temporary CSV files cleaned up.")
        print(f"[INFO] Kept {self.keep_data} CSV files, removed {self.snake_population_size-self.keep_data}.")

    def step(self):
        """Advance the model by one step."""
        # This function psuedo-randomly reorders the list of agent objects and
        # then iterates through calling the function passed in as the parameter
        self.set_time()
        self.set_temperatures()
        self.agents.shuffle_do("step")
        self.step_id += 1

    def run_model(self, max_steps=None):
        if max_steps is None:
            max_steps = len(self.thermal_profile)

        start_time = time.perf_counter()

        for _ in range(max_steps):
            if not self.running:
                break
            self.step()
        self.running = False
        self.summarize_simulation()

        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"Model run completed in {elapsed:.2f} seconds.")

        return



if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results')
    db_path = os.path.join(output_directory, 'suffugium.db')
    sim_id = 1
    model = Suffugium(config=config_path, output_directory=output_directory, sim_id=sim_id, seed=42)
    print(f"Model initialized")
    model.run_model()
    print(f"Run Complete")



