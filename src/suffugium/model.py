import numpy as np
import mesa
import yaml
import os
from config_schema import RootConfig
import polars as pl
from organism import Rattlesnake

class Suffugium(mesa.Model):
    '''A model for simulating the survival of ectotherms at a given location.'''
    def __init__(self, sim_id, config, output_directory, seed=None):
        super().__init__(seed=seed)
        self.sim_id = sim_id
        if output_directory is not None:
            os.makedirs(output_directory, exist_ok=True)
            self.output_directory = output_directory
        else:
            self.output_directory = ''
        with open(config, "r") as f:
            _config = yaml.safe_load(f)
        self.config = RootConfig.model_validate(_config)
        self.study_site = self.config.Model_Parameters.Site
        self.experiment = self.config.Model_Parameters.Experiment
        self.experiment_name = f"{self.study_site}_{self.experiment}"
        self.microhabitats = ['Burrow', 'Open']
        self.thermal_profile = pl.read_csv(self.config.Landscape_Parameters.Thermal_Database_fp)
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
        burrow_temp = self.open_temp_vector.row(self.step_id)[0]
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


    def step(self):
        """Advance the model by one step."""
        # This function psuedo-randomly reorders the list of agent objects and
        # then iterates through calling the function passed in as the parameter
        self.set_time()
        self.set_temperatures()
        self.agents.shuffle_do("step")
        self.step_id += 1


if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results')
    sim_id = 1
    model = Suffugium(config=config_path, output_directory=output_directory, sim_id=sim_id, seed=42)
    print(f"Model initialized")
    steps = 10
    for i in range(steps):
        print(model.get_timestamp())
        model.step()


