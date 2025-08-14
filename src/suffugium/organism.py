from mesa import Agent
import numpy as np
import json
import math
import behavior
import metabolism
from scipy.stats import truncnorm
import data_logger as dl

def set_value_truncnorm(mean, std, min_value, max_value):
    a, b = (min_value - mean) / std, (max_value - mean) / std
    return float(truncnorm.rvs(a, b, loc=mean, scale=std))

class Rattlesnake(Agent):
    """An abstract class representing an organism in the simulation."""
    
    def __init__(self,model, config, interaction_config):
        super().__init__(model)
        self.config = config
        self.interaction_config = interaction_config
        self.age = 0  # Age in days
        self._active = False
        self._alive = True
        self._cause_of_death  = None  
        self._current_behavior = 'Rest'  # Initial behavior
        self._current_microhabitat = 'Burrow'  # Initial microhabitat
        self._body_temperature = self.config.Initial_Body_Temperature  # Initial body temperature
        self._t_env = 0
        self._thermal_accuracy = 0
        self._thermal_quality = 0
        self.searching_behavior = self.interaction_config.searching_behavior
        self.brumation_period = self.get_brumination_period(self.model.config.Rattlesnake_Parameters.brumation.file_path)
        self.strike_performance = self.config.strike_performance
        #self.max_thermal_accuracy =self.config.utility.max_thermal_accuracy
        self.brumation_temp = self.config.brumation.temperature
        self.behavior_module = behavior.EctothermBehavior(self, interaction_config)
        self.metabolism = metabolism.EctothermMetabolism(org=self,
                                                model=self.model, 
                                                initial_metabolic_state=self.config.initial_calories, 
                                                max_meals=self.config.utility.max_meals, 
                                                X1_mass=self.config.smr.X1_mass,
                                                X2_temp=self.config.smr.X2_temp, 
                                                X3_const=self.config.smr.X3_const,
                                                prey_body_size=interaction_config.expected_prey_body_size,
                                                calories_per_gram=interaction_config.calories_per_gram)
        self.active_hours = self.config.active_hours
        self.activity_coefficients = self.config.behavior_activity_coefficients
        self.set_body_size()
        self.initialize_thermal_preference()
        self.initialize_ct_boundary()
        self.data_logger = dl.DataLogger(model=self.model, snake=self)
        self.data_logger.make_file()
        self.data_logger.log_data() # Initial log entry


    @property
    def species_name(self):
        """Returns the class name as a string."""
        return self.__class__.__name__
    
    @property
    def cause_of_death(self):
        '''Returns the cause of death if the organism is dead, otherwise None.'''
        if not self.alive:
            return self._cause_of_death
        return None
    
    @cause_of_death.setter
    def cause_of_death(self, value):
        if not self.alive:
            raise ValueError("Cannot set cause of death for a living organism.")
        self._cause_of_death = value

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

    @property
    def thermal_accuracy(self):
        return self._thermal_accuracy

    @thermal_accuracy.setter
    def thermal_accuracy(self, value):
        self._thermal_accuracy = value

    @property
    def thermal_quality(self):
        return self._thermal_quality

    @thermal_quality.setter
    def thermal_quality(self, value):
        self._thermal_quality = value

    def initialize_thermal_preference(self):
        """Initialize the thermal preference parameters."""
        self.k = self.config.thermal_preference.k
        self.t_pref_min = self.config.thermal_preference.t_pref_min
        self.t_pref_max = self.config.thermal_preference.t_pref_max
        self.t_opt = self.config.thermal_preference.t_opt
        self.delta_t = self.config.delta_t

    def initialize_ct_boundary(self):
        self.ct_min = self.config.voluntary_ct.min_temp
        self.ct_max = self.config.voluntary_ct.max_temp
        self.ct_max_steps = self.config.voluntary_ct.max_steps
        self.ct_out_of_bounds_tcounter = 0

    def set_body_size(self):
        mean_val = self.config.body_size_config.mean
        std_val = self.config.body_size_config.std
        min_val = self.config.body_size_config.min
        max_val = self.config.body_size_config.max
        self.body_size = set_value_truncnorm(mean=mean_val, std=std_val, min_value=min_val, max_value=max_val)

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
            t_env = self.model.burrow_temperature
        elif current_microhabitat=='Open':
            t_env = self.model.open_temperature
        elif current_microhabitat=='Winter_Burrow':
            t_env = self.brumation_temp
        else:
            raise ValueError('Microhabitat Property Value cant be found')
        return t_env
    
    def update_body_temp(self):
        old_body_temp = self.body_temperature
        self.t_env = self.get_t_env(self.current_microhabitat)
        self.body_temperature = self.cooling_eq_k(k=self.k, t_body=self.body_temperature, t_env=self.t_env, delta_t=self.delta_t)
        return
    
    def check_ct_out_of_bounds(self):
        if self.body_temperature < self.ct_min:
            self.ct_out_of_bounds_tcounter += 1
            if self.ct_out_of_bounds_tcounter >= self.ct_max_steps:
                self.alive = False
                self._cause_of_death = 'Cold'
        elif self.body_temperature > self.ct_max:
            self.ct_out_of_bounds_tcounter += 1
            if self.ct_out_of_bounds_tcounter >= self.ct_max_steps:
                self.alive = False
                self._cause_of_death = 'Heat'
        else:
            self.ct_out_of_bounds_tcounter = 0

    def calculate_thermal_accuracy(self):
        """Calculate the thermal accuracy based on the current body temperature."""
        return np.abs(self.body_temperature - self.t_opt)
    
    def calculate_thermal_quality(self):
        """Calculate the thermal quality based on the current body temperature."""
        return np.abs(self.t_env - self.t_opt)

    def is_starved(self):
        '''
        Internal state function to switch the state of the agent from alive to dead when their energy drops below 0.
        '''
        if self.metabolism.metabolic_state<=0:
            self.alive = False
            self.cause_of_death = 'Starved'

    def check_if_dead(self):
        """
        Check if the organism is dead and update its state accordingly.
        """
        if not self.alive:
            self.model.remove_agent(self)
            

    def step(self):
        """Advance the organism's state by one step."""
        self.age += 1
        self.behavior_module.step()
        ac = self.get_activity_coefficent()
        self.metabolism.cals_lost(mass=self.body_size, temperature=self.body_temperature, activity_coefficient = ac)
        self.update_body_temp()
        self.thermal_accuracy = self.calculate_thermal_accuracy()
        self.thermal_quality = self.calculate_thermal_quality()
        self.is_starved()
        self.check_ct_out_of_bounds()
        self.data_logger.log_data()
        self.check_if_dead()
        print(f"Organism {self.unique_id}- bt is {self.body_temperature}, behavior: {self.current_behavior}, microhabitat: {self.current_microhabitat}")
