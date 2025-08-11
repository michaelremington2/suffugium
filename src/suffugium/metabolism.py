import numpy as np
import matplotlib.pyplot as plt
from numba import njit, prange

class EctothermMetabolism(object):
    def __init__(self, org, model, initial_metabolic_state, max_meals, X1_mass, X2_temp, X3_const):
        self.org = org
        self.model = model
        self.mlo2_to_joules = 19.874
        self.joules_to_cals = 2.39e-4
        self.X1_mass = X1_mass
        self.X2_temp = X2_temp
        self.X3_const = X3_const
        self._metabolic_state = None
        self.metabolic_state = initial_metabolic_state
        self.max_meals = max_meals
        self.initialize_max_metabolic_state()

    @property
    def metabolic_state(self):
        return self._metabolic_state

    @metabolic_state.setter
    def metabolic_state(self, value):
        if isinstance(value, (list, tuple)) and len(value) == 2:
            self._metabolic_state = float(np.random.uniform(value[0], value[1]))
        elif isinstance(value, range):
            self._metabolic_state = float(np.random.uniform(value.start, value.stop))
        elif isinstance(value, (int, float)):
            self._metabolic_state = float(value)
        else:
            raise ValueError("`metabolic_state` must be a range, list, tuple, or single numeric value.")

    def initialize_max_metabolic_state(self):
        predator_label = self.org.species_name
        prey_label = self.model.interaction_map.get_prey_for_predator(predator_label=predator_label)[0]
        calories_per_gram = self.model.interaction_map.get_calories_per_gram(predator=predator_label, prey=prey_label)
        expected_prey_body_size = self.model.interaction_map.get_expected_prey_body_size(predator=predator_label, prey=prey_label)
        self.max_metabolic_state = self.max_meals * calories_per_gram * expected_prey_body_size

    @staticmethod
    @njit
    def smr_eq(mass, temperature, X1_mass, X2_temp, X3_const):
        '''Compute SMR (VO2 proxy) using allometrically scaled equation'''
        log_smr = (X1_mass * np.log10(mass)) + (X2_temp * temperature) + X3_const
        smr = 10**log_smr
        return smr

    @staticmethod
    @njit
    def hourly_energy_expenditure(smr, activity_coefficient, mlo2_to_joules, joules_to_cals):
        '''Compute hourly energy expenditure in calories'''
        hee = smr * activity_coefficient
        joules_per_hour = hee * mlo2_to_joules
        return joules_per_hour * joules_to_cals

    @staticmethod
    @njit
    def energy_intake(prey_mass, cal_per_gram_conversion, percent_digestion_cals):
        '''Compute calories gained from prey ingestion'''
        return prey_mass * cal_per_gram_conversion * percent_digestion_cals

    def energy_expenditure_graph(self):
        '''Figure for visualizing an individual's metabolism'''
        mass_values = np.linspace(800, 5000, 100)  
        temperature_values = np.linspace(5, 40, 100)  
        
        smr_values = np.zeros((len(mass_values), len(temperature_values)))
        energy_resting = np.zeros_like(smr_values)
        energy_foraging = np.zeros_like(smr_values)

        for i in range(len(mass_values)):
            for j in range(len(temperature_values)):
                smr_values[i, j] = self.smr_eq(mass_values[i], temperature_values[j], self.X1_mass, self.X2_temp, self.X3_const)
                energy_resting[i, j] = self.hourly_energy_expenditure(smr_values[i, j], 1, self.mlo2_to_joules, self.joules_to_cals)
                energy_foraging[i, j] = self.hourly_energy_expenditure(smr_values[i, j], 1.5, self.mlo2_to_joules, self.joules_to_cals)

        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        for ax, data, title in zip(axes, [energy_resting, energy_foraging], ["Resting", "Foraging"]):
            contour = ax.contourf(mass_values, temperature_values, data.T, cmap='viridis', levels=20)
            fig.colorbar(contour, ax=ax, label=f'{title} Energy Exp.')
            ax.set_title(f'{title} Energy Expenditure')
            ax.set_xlabel('Body Mass (g)')
            ax.set_ylabel('Temperature (°C)')
        
        plt.tight_layout()
        plt.show()

    def cals_lost(self, mass, temperature, activity_coefficient):
        '''Compute and deduct calories lost from metabolic state'''
        smr = self.smr_eq(mass, temperature, self.X1_mass, self.X2_temp, self.X3_const)
        cals_spent = self.hourly_energy_expenditure(smr, activity_coefficient, self.mlo2_to_joules, self.joules_to_cals)
        self.metabolic_state -= cals_spent

    def cals_gained(self, prey_mass, cal_per_gram_conversion, percent_digestion_cals):
        '''Compute and add calories gained to metabolic state'''
        cals_gained = self.energy_intake(prey_mass, cal_per_gram_conversion, percent_digestion_cals)
        self.metabolic_state += cals_gained
