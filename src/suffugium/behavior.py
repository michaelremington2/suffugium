import numpy as np
#import ThermaNewt.sim_snake_tb as tn
from math import isclose
from numba import njit


def sparsemax(z):
    """
    Sparsemax: projects input vector z onto probability simplex with possible sparsity.
    Assumes z is a 1D array scaled to reasonable range (e.g., [0,1]).
    """
    z = np.asarray(z, dtype=np.float64)

    # Sort z in descending order
    z_sorted = np.sort(z)[::-1]
    k = np.arange(1, len(z) + 1)  # 1-based indexing for algorithm
    
    # Determine k_max: largest k where threshold holds
    z_cumsum = np.cumsum(z_sorted)
    condition = 1 + k * z_sorted > z_cumsum
    if not np.any(condition):
        # fallback: uniform distribution if no support found
        return np.ones_like(z) / len(z)
    k_z = k[condition][-1]
    
    # Compute threshold tau
    tau_z = (z_cumsum[k_z - 1] - 1) / k_z

    # Compute projection onto simplex
    p = np.maximum(z - tau_z, 0)
    p /= p.sum()  # ensure probabilities sum to 1 for numerical stability
    return p


def set_value_uniform(min_value, max_value):
    return float(np.random.uniform(min_value, max_value))

class EctothermBehavior(object):
    def __init__(self, snake, interaction_config):
        self.snake = snake
        self.model = self.snake.model
        self.interaction_config = interaction_config
        self._attack_rate = 0
        self._handling_time = 0
        self._prey_density = 0
        self._strike_performance = 0
        self._prey_encountered = 0
        self._prey_consumed = 0
        self._search_counter = 0
        self.attack_rate = self.set_attack_rate()
        self.prey_density = self.set_prey_density()
        self.handling_time = self.interaction_config.handling_time
        self.calories_per_gram = self.interaction_config.calories_per_gram
        self.digestion_efficiency = self.interaction_config.digestion_efficiency
        self.prey_active_hours = self.interaction_config.prey_active_hours
        self.prey_body_size = self.interaction_config.expected_prey_body_size
        self.searching_behavior = self.interaction_config.searching_behavior
        self.emergent_behaviors = ['Rest', 'Thermoregulate', 'Forage']

    @property
    def prey_density(self):
        if self.model.hour in self.prey_active_hours:
            return self._prey_density
        else:
            return 0

    @prey_density.setter
    def prey_density(self, value):
        self._prey_density = value

    @property
    def attack_rate(self):
        return self._attack_rate

    @attack_rate.setter
    def attack_rate(self, value):
        self._attack_rate = value

    @property
    def handling_time(self):
        return self._handling_time

    @handling_time.setter
    def handling_time(self, value):
        self._handling_time = value

    @property
    def prey_encountered(self):
        return self._prey_encountered

    @prey_encountered.setter
    def prey_encountered(self, value):
        self._prey_encountered = value

    @property
    def prey_consumed(self):
        return self._prey_consumed

    @prey_consumed.setter
    def prey_consumed(self, value):
        self._prey_consumed = value

    @property
    def search_counter(self):
        return self._search_counter

    @search_counter.setter
    def search_counter(self, value):
        self._search_counter = value

    def set_attack_rate(self):
        """Set the attack rate based on interaction parameters."""
        return np.round(set_value_uniform(
            min_value=self.interaction_config.attack_rate_range.min,
            max_value=self.interaction_config.attack_rate_range.max
        ), decimals=3)
    
    def set_prey_density(self):
        """Set the prey density based on interaction parameters."""
        return np.round(set_value_uniform(
            min_value=self.interaction_config.prey_density_range.min,
            max_value=self.interaction_config.prey_density_range.max
        ),decimals=0)

    def thermal_accuracy_calculator(self):
        '''Calculate thermal accuracy'''
        return np.abs(float(self.snake.t_opt) - float(self.snake.body_temperature))
    
    def get_metabolic_state_variables(self):
        return self.snake.metabolism.metabolic_state, self.snake.metabolism.max_metabolic_state
    
    @staticmethod
    @njit
    def scale_value(value, max_value):
        '''Numba-optimized function to normalize values between 0 and 1'''
        x = value / max_value
        return min(x, 1.0)
    
    def calc_thermoregulation_utility(self):
        """Calculate the utility of thermoregulation based on thermal accuracy."""
        db = self.thermal_accuracy_calculator()
        if self.snake.body_temperature < self.snake.t_opt:
            denominator = self.snake.t_opt - self.snake.t_pref_min
        else:
            denominator = self.snake.t_pref_max - self.snake.t_opt

        return self.scale_value(db, denominator)

    @staticmethod
    @njit
    def holling_type_2(prey_density, attack_rate, handling_time, strike_success=1):
        """
        Computes the Holling Type II functional response.

        Parameters:
        - prey_density (float): Prey density per hectare
        - attack_rate (float): Area searched per predator per time unit
        - handling_time (float): Handling time per prey item
        - strike_success (float): Probability of a successful strike.
            Default of 1: Use this argument to calculate number of encounters
            less than 1: Function calculates successful prey items caught.

        Returns:
        - Expected number of prey consumed per predator per time unit
        """
        if strike_success>1:
            raise(ValueError("Strike success is a probability that cant exceed 1"))
        return ((strike_success * attack_rate) * prey_density) / (1 + (strike_success * attack_rate) * handling_time * prey_density)

    def forage(self):
        '''Foraging behavior logic with optimized functional response calculations'''
        self.snake.current_microhabitat = 'Open'
        self.snake.current_behavior = 'Forage'
        self.snake.active = True

        prey_encountered = self.holling_type_2(prey_density = self.prey_density,  attack_rate = self.attack_rate, handling_time =self.handling_time, strike_success=self.snake.strike_performance)
        self.prey_encountered += prey_encountered
        self.prey_consumed = int(np.random.poisson(prey_encountered)) 
        if self.prey_consumed> 0:
            self.snake.metabolism.cals_gained(self.prey_body_size, self.calories_per_gram, self.digestion_efficiency)
            if self.snake.searching_behavior:
                self.snake.search_counter = (self.handling_time-1)


    def rest(self):
        '''Resting behavior'''
        self.snake.current_microhabitat = 'Burrow'
        self.snake.current_behavior = 'Rest'
        self.snake.active = False

    def search(self):
        '''looking for a prey item that has been hit behavior'''
        self.snake.current_microhabitat = 'Open'
        self.snake.current_behavior = 'Search'
        self.snake.active = True
        self.search_counter -= 1

    def bruminate(self):
        '''overwintering behavior'''
        self.snake.current_microhabitat = 'Winter_Burrow'
        self.snake.current_behavior = 'Brumation'
        self.snake.body_temperature = self.snake.brumation_temp
        self.snake.active = False

    ## Thermoregulation calculation
    # def calc_prob_preferred_topt(self, t_body, t_pref_opt, t_pref_max, t_pref_min):
    #     if t_body >= t_pref_opt:
    #         prob_flip = ((t_body - t_pref_opt) / (t_pref_max - t_pref_opt))
    #     elif t_body < t_pref_opt:
    #         prob_flip = ((t_pref_opt - t_body) / (t_pref_opt - t_pref_min))
    #     else:
    #         raise ValueError("Something is messed up")
    #     if prob_flip > 1:
    #         prob_flip = 1
    #     return prob_flip

    def thermoregulation_select_microhabitat(self, t_body,burrow_temp, open_temp):
        if t_body > self.snake.t_opt and burrow_temp < open_temp:
            flip_direction = 'Burrow'
        elif t_body < self.snake.t_opt and burrow_temp > open_temp:
            flip_direction = 'Burrow'
        else:
            flip_direction = 'Open'
        return flip_direction
    
    # def preferred_topt(self, t_body, burrow_temp, open_temp):
    #     """Determines if the snake should switch microhabitats based on preferred temperatures."""
        
    #     # Calculate the probability of flipping microhabitats based on the snake's body temperature.
    #     prob_flip = self.calc_prob_preferred_topt(
    #         t_body=t_body,
    #         t_pref_opt=self.snake.t_opt,
    #         t_pref_max=self.snake.t_pref_max, 
    #         t_pref_min=self.snake.t_pref_min
    #     )  

    #     # If the body temperature is nearly optimal OR the two microhabitat temperatures are nearly equal,
    #     # retain the current state (or randomly choose if not set).
    #     if isclose(t_body, self.snake.t_opt, abs_tol=0.01) or isclose(burrow_temp, open_temp, abs_tol=0.01):
    #         return self.snake.current_microhabitat

    #     # Decide to flip microhabitats based on a random draw and the calculated probability.
    #     if np.random.random() <= prob_flip:
    #         bu = self.best_habitat_t_opt(t_body = t_body, burrow_temp=burrow_temp, open_temp=open_temp)
    #         return bu
    #     else: 
    #         return self.snake.current_microhabitat


    def thermoregulate(self):
        '''Thermoregulation behavior based on preferred sub module'''
        self.snake.current_behavior = 'Thermoregulate'
        self.snake.active = True
        mh = self.thermoregulation_select_microhabitat(
            t_body=self.snake.body_temperature,
            burrow_temp=self.snake.model.burrow_temperature,
            open_temp=self.snake.model.open_temperature
        )
        self.snake.current_microhabitat = mh
        
    # Behavioral Algorithm
    def set_utilities(self):
        '''Calculate utilities for behavior selection'''
        if self.model.hour in self.snake.active_hours:
            db = self.thermal_accuracy_calculator()
            metabolic_state, max_metabolic_state = self.get_metabolic_state_variables()
            thermoregulate_utility = self.calc_thermoregulation_utility()
            rest_utility = self.scale_value(metabolic_state, max_metabolic_state)
            forage_utility = 1 - rest_utility
        else:
            rest_utility = 1
            thermoregulate_utility = 0
            forage_utility = 0
        return np.array([rest_utility, thermoregulate_utility, forage_utility])
    
    # Changing from softmax to sparsemax for behavioral weights
    # def set_behavioral_weights(self,utl_temperature=1.0):
    #     utilities = self.set_utilities()
    #     if np.allclose(utilities, 0):
    #         return np.ones_like(utilities) / len(utilities)  # Avoid divide-by-zero
    #     masked_utilities = np.where(utilities == 0, -np.inf, utilities)
    #     return softmax(masked_utilities / utl_temperature)

        # def choose_behavior(self):
    #     behavior_probabilities = self.set_behavioral_weights(utl_temperature=self.snake.utility_temperature)
    #     return np.random.choice(self.snake.emergent_behaviors, p=behavior_probabilities)

    def set_behavioral_weights(self):
        '''Calculate sparsemax-based probabilities for behavior selection'''
        utilities = self.set_utilities()
        if np.allclose(utilities, 0):
            return np.ones_like(utilities) / len(utilities)  # Avoid divide-by-zero
        return sparsemax(utilities)
    
    def reset_prey_consumed(self):
        '''Reset the prey consumed counter at the end of the day'''
        self.prey_consumed = 0

    
    def choose_behavior(self):
        '''Choose a behavior stochastically from sparsemax probabilities'''
        self.reset_prey_consumed() 
        behavior_probabilities = self.set_behavioral_weights()
        return np.random.choice(self.emergent_behaviors, p=behavior_probabilities)

    def step(self):
        '''Handles picking and executing behavior functions'''
        if self.snake.is_bruminating_today():
            self.bruminate()
        elif self.model.hour not in self.snake.active_hours:
            self.rest()
        elif self.snake.ct_out_of_bounds_tcounter>0:
            self.thermoregulate()
        elif self.search_counter > 0:
            self.search()
        else:
            behavior = self.choose_behavior()
            behavior_actions = {
                'Rest': self.rest,
                'Thermoregulate': self.thermoregulate,
                'Forage': self.forage,
            }
            behavior_actions.get(behavior, lambda: ValueError(f"Unknown behavior: {behavior}"))()
