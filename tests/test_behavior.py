import pytest
from unittest.mock import Mock
import numpy as np
from suffugium.behavior import EctothermBehavior
from suffugium.config_schema import InteractionParameters


@pytest.fixture
def behavior():
    """Fixture for creating an instance of EctothermMetabolism with made up numbers."""
    snake = Mock()
    snake.body_size = 300 
    snake.body_temperature = 25
    snake.model = Mock()
    interaction_config_dict = {
                "calories_per_gram": 1.38,
                "digestion_efficiency": 0.8,
                "expected_prey_body_size": 70,
                "handling_time": 2,
                "attack_rate_range": {
                    "min": 0.0001,
                    "max": 0.01
                },
                "prey_density_range": {
                    "min": 1,
                    "max": 22
                },
                "searching_behavior": True,
                "prey_active_hours": [20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]
            }
    interaction_config = InteractionParameters.model_validate(interaction_config_dict)
    return EctothermBehavior(snake=snake, interaction_config=interaction_config)

def test_initialization(behavior):
    """Test that the initial metabolic state is set correctly."""
    assert behavior.prey_body_size == 70

def test_prey_density_off_hours(behavior):
    """Test that prey density is calculated correctly durring inactive hours."""
    behavior.snake.model.hour = 12
    assert behavior.prey_density == 0

def test_prey_density_on_hours(behavior):
    """Test that prey density is calculated correctly durring active hours."""
    behavior.snake.model.hour = 20
    assert 0 < behavior.prey_density <= 22

def test_attack_rate(behavior):
    """Test that the attack rate is calculated correctly."""
    assert 0.0001 <= behavior.attack_rate <= 0.01

def test_thermal_accuracy_calculator(behavior):
    behavior.snake.body_temperature = 30
    behavior.snake.t_opt = 29
    accuracy = behavior.thermal_accuracy_calculator()
    assert accuracy == 1

def test_calc_thermoregulation_utility(behavior):
    """Test the calculation of thermoregulation utility."""
    behavior.snake.body_temperature = 30
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    utility = behavior.calc_thermoregulation_utility()
    print(utility)
    assert utility == 0.5

def test_holling_type_2(behavior):
    strike_success = 1
    prey_density = 1
    attack_rate = 1
    handling_time = 1
    prey_caught = behavior.holling_type_2(prey_density=prey_density,
                                          attack_rate=attack_rate,
                                          handling_time=handling_time,
                                          strike_success=strike_success)
    assert prey_caught == 0.5

def test_thermoregulation_select_microhabitat_burrow(behavior):
    '''Test whether snake uses burrow when appropriate'''
    burrow_temp = 10
    open_temp = 30
    behavior.snake.body_temperature = 30
    behavior.snake.t_opt = 29
    microhabitat = behavior.thermoregulation_select_microhabitat(t_body = behavior.snake.body_temperature,
    burrow_temp=burrow_temp,
    open_temp=open_temp)
    assert microhabitat == 'Burrow'

def test_thermoregulation_select_microhabitat_open(behavior):
    '''Test whether snake uses open when appropriate'''
    burrow_temp = 10
    open_temp = 30
    behavior.snake.body_temperature = 15
    behavior.snake.t_opt = 29
    microhabitat = behavior.thermoregulation_select_microhabitat(t_body = behavior.snake.body_temperature,
    burrow_temp=burrow_temp,
    open_temp=open_temp)
    assert microhabitat == 'Open'

def test_set_utilities_forage(behavior):
    behavior.snake.metabolism.metabolic_state = 5
    behavior.snake.metabolism.max_metabolic_state = 100
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 20
    behavior.snake.body_temperature = 29
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    utility_vector = behavior.set_utilities()
    rest_utility = utility_vector[0]
    thermoregulate_utility = utility_vector[1]
    forage_utility = utility_vector[2]
    assert thermoregulate_utility==0
    assert rest_utility < forage_utility <=1

def test_set_utilities_forage(behavior):
    behavior.snake.metabolism.metabolic_state = 100
    behavior.snake.metabolism.max_metabolic_state = 100
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 20
    behavior.snake.body_temperature = 29
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    utility_vector = behavior.set_utilities()
    rest_utility = utility_vector[0]
    thermoregulate_utility = utility_vector[1]
    forage_utility = utility_vector[2]
    assert rest_utility ==1
    assert forage_utility == (1-rest_utility)

def test_set_utilities_thermoregulate(behavior):
    behavior.snake.metabolism.metabolic_state = 100
    behavior.snake.metabolism.max_metabolic_state = 100
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 20
    behavior.snake.body_temperature = 30
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    utility_vector = behavior.set_utilities()
    rest_utility = utility_vector[0]
    thermoregulate_utility = utility_vector[1]
    forage_utility = utility_vector[2]
    assert thermoregulate_utility == 0.5

def test_set_utilities_inactive(behavior):
    behavior.snake.metabolism.metabolic_state = 100
    behavior.snake.metabolism.max_metabolic_state = 100
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 10
    behavior.snake.body_temperature = 30
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    utility_vector = behavior.set_utilities()
    rest_utility = utility_vector[0]
    thermoregulate_utility = utility_vector[1]
    forage_utility = utility_vector[2]
    assert rest_utility == 1
    assert thermoregulate_utility == 0
    assert forage_utility == 0

def test_choose_behavior(behavior):
    behavior.snake.metabolism.metabolic_state = 1
    behavior.snake.metabolism.max_metabolic_state = 1000
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 20
    behavior.snake.body_temperature = 29
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    snake_task = behavior.choose_behavior()
    assert snake_task=='Forage'

def test_choose_behavior_rest_thermoregulate(behavior):
    behavior.snake.metabolism.metabolic_state = 100
    behavior.snake.metabolism.max_metabolic_state = 100
    behavior.snake.active_hours = [20,21,22]
    behavior.snake.model.hour = 20
    behavior.snake.body_temperature = 10
    behavior.snake.t_opt = 29
    behavior.snake.t_pref_max = 31
    behavior.snake.t_pref_min = 19
    snake_task = behavior.choose_behavior()
    assert snake_task in ['Rest', 'Thermoregulate']

