import numpy as np
import mesa
import yaml
import os
from config_schema import RootConfig

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
        self.initialize_landscape()

    def initialize_landscape(self):
        """Initialize the landscape based on the configuration."""
        if self.config.Landscape_Parameters.spatially_explicit:
            raise NotImplementedError("Spatially explicit landscapes are not yet implemented.")
        else:
            from landscape import Spatially_Implicit_Landscape
            # Each snake gets a cell, No movment, so cell_count = population_size
            cell_count = self.config.Model_Parameters.agents.Rattlesnake
            self.landscape = Spatially_Implicit_Landscape(
                model=self,
                cell_count=cell_count,
                thermal_profile_csv_fp=self.config.Landscape_Parameters.Thermal_Database_fp
            )
            print(f"Landscape initialized with {cell_count} cells.")
           


if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results')
    model = Suffugium(config=config_path, output_directory=output_directory, seed=42)
    print(f"Model initialized")


