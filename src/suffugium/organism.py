from mesa import Agent
import numpy as np
import json

class Rattlesnake(Agent):
    """An abstract class representing an organism in the simulation."""
    
    def __init__(self,model, config, interaction_config):
        super().__init__(model)
        self.config = config
        self.interaction_config = interaction_config
        self.calories = 100  # Initial calories
        self.age = 0  # Age in days
        self._active = False
        self._alive = True
        self._cause_of_death  = None
        self.brumation_period = self.get_brumination_period(self.model.config.Rattlesnake_Parameters.brumation.file_path)
        self.brumation_temp = self.model.config.Rattlesnake_Parameters.brumation.temperature
        self._current_behavior = 'Rest'  # Initial behavior
        self._current_microhabitat = 'Burrow'  # Initial microhabitat
        self._body_temperature = 25  # Initial body temperature


    @property
    def species_name(self):
        """Returns the class name as a string."""
        return self.__class__.__name__

    @property
    def current_behavior(self):
        return self._current_behavior

    @current_behavior.setter
    def current_behavior(self, value):
        self._current_behavior = value

    @property
    def current_microhabitat(self):
        return self._current_microhabitat

    @current_microhabitat.setter
    def current_microhabitat(self, value):
        self._current_microhabitat = value

    @property
    def body_temperature(self):
        return self._body_temperature

    @body_temperature.setter
    def body_temperature(self, value):
        if self.is_bruminating_today():
            self._body_temperature = self.brumation_temp
        else:
            self._body_temperature = value

    @property
    def t_env(self):
        return self._t_env

    @t_env.setter
    def t_env(self, value):
        self._t_env = value

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        # Force inactivity if agent is dead or in brumation
        if not self.alive:
            self._active = False
        elif self.current_microhabitat=='Burrow':
            self._active = False
        elif self.current_behavior == 'Rest':
            self._active = False
        elif self.current_behavior == 'Thermoregulate':
            self._active = True
        elif self.current_behavior == 'Forage':
            self._active = True
        elif self.is_bruminating_today():
            self._active = False
        else:
            self._active = bool(value)  # Ensures it's explicitly True/False

    @property
    def alive(self):
        return self._alive

    @alive.setter
    def alive(self, value):
        self._alive = value
        if value==False:
            self.active=False

    def get_brumination_period(self, file_path):
        '''
        Function to read in the brumation period from a JSON file
        and convert date strings into (month, day) tuples.
        '''
        with open(file_path, 'r') as f:
            data = json.load(f) 
        if len(data) != 1:
            raise ValueError("JSON must contain exactly one site entry.")
        site_name = list(data.keys())[0]
        date_strs = data[site_name]
        # if site_name != self.model.landscape.site_name:
        #     raise ValueError(
        #         f"Site name in JSON file '{site_name}' does not match model site name '{self.model.landscape.site_name}'."
        #     )
        return [
            (int(date.split('-')[0]), int(date.split('-')[1]))
            for date in date_strs
        ]

    def is_bruminating_today(self):
        return (self.model.month, self.model.day) in self.brumation_period
    
    def activate_snake(self):
        if self.current_behavior in ['Thermoregulate', 'Forage', 'Search']:
            self.active = True
        else:
            self.active = False

    def get_activity_coefficent(self):
        return self.activity_coefficients[self.current_behavior]

    def cooling_eq_k(self, k, t_body, t_env, delta_t):
        exp_decay = math.exp(-k*delta_t)
        return t_env+(t_body-t_env)*exp_decay
    
    def get_t_env(self, current_microhabitat):
        if current_microhabitat=='Burrow':
            t_env = self.model.landscape.burrow_temperature
        elif current_microhabitat=='Open':
            t_env = self.model.landscape.open_temperature
        elif current_microhabitat=='Winter_Burrow':
            t_env = self.brumation_temp
        else:
            raise ValueError('Microhabitat Property Value cant be found')
        return t_env
    
    def update_body_temp(self, t_env):
        old_body_temp = self.body_temperature
        self.body_temperature = self.cooling_eq_k(k=self.k, t_body=self.body_temperature, t_env=t_env, delta_t=self.delta_t)
        return

    def step(self):
        """Advance the organism's state by one step."""
        self.age += 1
        print("hello from organism step")
