import polars as pl
import numpy as np
import csv


class DataLogger(object):
    '''Class for reporting data of snakes in the simulation.'''
    def __init__(self, model, snake):
        self.model = model
        self.snake = snake
        self.header = ['Step', 'Agent_ID', 'Experiment_Name', 'Study_site', 'Experiment', 'Hour', 'Day', 'Month', 'Season', 'Year','Alive','Active', 'Mass', 'Behavior', 'Microhabitat', 'Body_Temperature', 'T_env', 'Metabolic_state','Prey_Density', 'Attack_Rate', 'Prey_Consumed', 'Cause_of_Death']

    def make_file_name(self):
        return f"{self.model.output_directory}/{self.snake.unique_id}_data_log.csv"
    
    def make_file(self):
        file_name = self.make_file_name()
        with open(file_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)

    def log_data(self):
        file_name = self.make_file_name()
        with open(file_name, 'a', newline='') as f:
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
                self.snake.body_temperature,
                self.snake.t_env,
                self.snake.metabolism.metabolic_state,
                self.snake.behavior_module.prey_density,
                self.snake.behavior_module.attack_rate,
                self.snake.behavior_module.prey_consumed,
                self.snake.cause_of_death,

            ])