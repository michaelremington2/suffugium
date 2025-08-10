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
        print(f"Config loaded: {cfg}")


if __name__ ==  "__main__":
    base_directory = '/home/micha/Documents/suffugium/'
    config_path = os.path.join(base_directory, 'config.yaml')
    output_directory = os.path.join(base_directory, 'results')
    model = Suffugium(config=config_path, output_directory=output_directory, seed=42)
    print(f"Model initialized")


