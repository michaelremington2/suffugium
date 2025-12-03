import polars as pl
import numpy as np
import csv


class DataLogger(object):
    '''Class for reporting data of snakes in the simulation.'''
    def __init__(self, model, snake):
        self.model = model
        self.snake = snake
        self.header = ['Step_id', 'Agent_ID', 'Experiment_Name', 'Study_site', 'Experiment', 'Hour', 'Day', 'Month', 'Season', 'Year','Alive','Active', 'Mass', 'Behavior', 'Microhabitat', 'Body_Temperature', 'T_env','Thermal_Accuracy', 'Thermal_Quality', 'Burrow_Temperature', 'Open_Temperature', 'Metabolic_state','Prey_Density', 'Attack_Rate', 'Prey_Consumed', 'Cause_of_Death','Sim_id','config_file_name']

    def make_file_name(self):
        return f"{self.model.temp_csvs_fp}/{self.snake.unique_id}_data_log.csv"
    
    def make_file(self):
        file_name = self.make_file_name()
        with open(file_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)

    def log_data(self):
        file_name = self.make_file_name()
        with open(file_name, 'a', newline='') as f:
            if self.snake.current_behavior=='Brumation':
                thermal_accuracy = None
                thermal_quality = None
                t_env = None
                body_temperature = None
            else:
                thermal_accuracy = self.snake.thermal_accuracy
                thermal_quality = self.snake.thermal_quality
                t_env = self.snake.t_env
                body_temperature = self.snake.body_temperature
            writer = csv.writer(f)
            writer.writerow([
                self.model.step_id,
                self.snake.unique_id,
                self.model.experiment_name,
                self.model.study_site,
                self.model.experiment,
                self.model.hour,
                self.model.day,
                self.model.month,
                self.model.get_season(),
                self.model.year,
                self.snake.alive,
                self.snake.active,
                self.snake.body_size,
                self.snake.current_behavior,
                self.snake.current_microhabitat,
                body_temperature,
                t_env,
                thermal_accuracy,
                thermal_quality,
                self.model.burrow_temperature,
                self.model.open_temperature,
                self.snake.metabolism.metabolic_state,
                self.snake.behavior_module.prey_density,
                self.snake.behavior_module.attack_rate,
                self.snake.behavior_module.prey_consumed,
                self.snake.cause_of_death,
                self.model.sim_id,
                self.model.config_file_name
            ])