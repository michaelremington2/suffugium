from mesa import agent
import numpy as np

class Organism(agent.Agent):
    """An abstract class representing an organism in the simulation."""
    
    def __init__(self, unique_id, model, body_size, body_temperature):
        super().__init__(unique_id, model)
        self.body_size = body_size  # Body size in grams
        self.body_temperature = body_temperature  # Body temperature in degrees Celsius
        self.calories = 100  # Initial calories
        self.age = 0  # Age in days

    def step(self):
        """Advance the organism's state by one step."""
        self.age += 1
        # Implement other behaviors such as foraging, thermoregulating, etc.