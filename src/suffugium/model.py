import numpy as np
import mesa
import yaml
import os
from config_schema import RootConfig
import polars as pl
from organism import Rattlesnake

class Suffugium(mesa.Model):
    '''A model for simulating the survival of ectotherms at a given location.'''
    def __init__(self,  config, output_directory, seed=None):
        super().__init__(seed=seed)
        if output_directory is not None:
            os.makedirs(output_directory, exist_ok=True)
            self.output_directory = output_directory
        else:
            self.output_directory = ''
        with open(config, "r") as f:
            _config = yaml.safe_load(f)
        self.config = RootConfig.model_validate(_config)
        self.microhabitats = ['Burrow', 'Open']
        self.thermal_profile = pl.read_csv(self.config.Landscape_Parameters.Thermal_Database_fp)
        self.env_columns = self.config.Landscape_Parameters.ENV_Temperature_Cols
        self.snake_population_size = self.config.Model_Parameters.agents.Rattlesnake
        self._burrow_temperature = None
        self._open_temperature = None
        self.initialize_population()
        self.step_id = 0

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
    
    def set_temperatures(self):
        # set these to env_cols
        open_temp = self.thermal_profile.select(self.env_columns.Open).row(self.step_id)[0]
        burrow_temp = self.thermal_profile.select(self.env_columns.Burrow).row(self.step_id)[0]
        self.open_temperature = open_temp
        self.burrow_temperature = burrow_temp

    def initialize_population(self):
        Rattlesnake.create_agents(model=self, 
                                  n=self.snake_population_size,
                                  config=self.config.Rattlesnake_Parameters,
                                  interaction_config=self.config.Interaction_Parameters)


    def step(self):
        """Advance the model by one step."""
        # This function psuedo-randomly reorders the list of agent objects and
        # then iterates through calling the function passed in as the parameter
        self.agents.shuffle_do("step")


if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results')
    model = Suffugium(config=config_path, output_directory=output_directory, seed=42)
    print(f"Model initialized")
    model.step()


