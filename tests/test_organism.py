import pytest
from unittest.mock import Mock
from suffugium.config_schema import InteractionParameters, RattlesnakeParameters
from suffugium.organism import Rattlesnake
import numpy as np


@pytest.fixture
def rattlesnake():
    """Fixture for creating an instance of the Rattlesnake object class with mock numbers."""
    Rattlesnake_Parameters_dict = {
                "species": "Rattlesnake",
                "body_size_config": {
                    "distribution": "normal",
                    "mean": 258.1,
                    "std": 86.6,
                    "min": 122,
                    "max": 575,
                },
                "active_hours": [17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                "Initial_Body_Temperature": 25,
                "initial_calories": 100,
                "utility": {
                    "max_meals": 3,
                },
                "thermal_preference": {
                    "k": 0.01,
                    "t_pref_min": 19,
                    "t_pref_max": 32,
                    "t_opt": 29,
                },
                "voluntary_ct": {
                    "min_temp": 5,
                    "max_temp": 45,
                    "max_steps": 2,
                },
                "strike_performance": 0.22,
                "delta_t": 60,
                "smr": {
                    "X1_mass": 0.93,
                    "X2_temp": 0.044,
                    "X3_const": -2.58,
                },
                "Brumation": {
                    "file_path": "/home/micha/Documents/suffugium/brumation_files/brumation_dates_Canada_1.json",
                    "scale": "Day",
                    "temperature": 10,
                },
                "behavior_activity_coefficients": {
                    "Rest": 1,
                    "Thermoregulate": 1.5,
                    "Forage": 1.5,
                    "Search": 1.5,
                    "Brumation": 1,
                },
            }
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
    snake_config = RattlesnakeParameters.model_validate(Rattlesnake_Parameters_dict)
    interaction_config = InteractionParameters.model_validate(interaction_config_dict)
    model = Mock()
    return Rattlesnake(model=model, config=snake_config, interaction_config=interaction_config, logging=False, brumation=False)

def test_body_size(rattlesnake):
    assert 122<=rattlesnake.body_size<=575

def test_activate_snake(rattlesnake):
    rattlesnake.current_behavior = 'Forage'
    rattlesnake.activate_snake()
    assert rattlesnake.active

def test_cooling_eq_k(rattlesnake):
    k=0.01
    delta_t=60
    t_env = 10
    t_body = 25
    expected_answer = 18.23
    answer = np.round(rattlesnake.cooling_eq_k(k=k,
                                               t_body=t_body,
                                               t_env=t_env,
                                               delta_t=delta_t),2)
    assert expected_answer == answer

def test_ct_cold_death_after_max_steps(rattlesnake):
    # Make it easy to trigger
    rattlesnake.ct_max_steps = 2
    rattlesnake.ct_out_of_bounds_tcounter = 0
    rattlesnake.alive = True

    # Below ct_min on two consecutive checks -> death by Cold
    rattlesnake.body_temperature = rattlesnake.ct_min - 0.1
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.alive is True
    assert rattlesnake.ct_out_of_bounds_tcounter == 1
    assert rattlesnake.cause_of_death is None

    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.alive is False
    assert rattlesnake.cause_of_death == "Cold"


def test_ct_heat_death_after_max_steps(rattlesnake):
    rattlesnake.ct_max_steps = 2
    rattlesnake.ct_out_of_bounds_tcounter = 0
    rattlesnake.alive = True

    # Above ct_max on two consecutive checks -> death by Heat
    rattlesnake.body_temperature = rattlesnake.ct_max + 0.1
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.alive is True
    assert rattlesnake.ct_out_of_bounds_tcounter == 1

    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.alive is False
    assert rattlesnake.cause_of_death == "Heat"


def test_ct_counter_resets_when_in_range(rattlesnake):
    rattlesnake.ct_max_steps = 3
    rattlesnake.ct_out_of_bounds_tcounter = 0
    rattlesnake.alive = True

    # 1st step: out of bounds (cold) increments counter
    rattlesnake.body_temperature = rattlesnake.ct_min - 5
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.ct_out_of_bounds_tcounter == 1
    assert rattlesnake.alive is True

    # Return to safe range -> counter resets to 0 and stays alive
    rattlesnake.body_temperature = (rattlesnake.ct_min + rattlesnake.ct_max) / 2
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.ct_out_of_bounds_tcounter == 0
    assert rattlesnake.alive is True
    assert rattlesnake.cause_of_death is None


def test_ct_bounds_are_inclusive(rattlesnake):
    """Exactly ct_min or ct_max should be considered IN range (no increment)."""
    rattlesnake.ct_out_of_bounds_tcounter = 1  # pre-load to ensure it resets
    rattlesnake.alive = True

    # Exactly ct_min
    rattlesnake.body_temperature = rattlesnake.ct_min
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.ct_out_of_bounds_tcounter == 0
    assert rattlesnake.alive is True

    # Exactly ct_max
    rattlesnake.ct_out_of_bounds_tcounter = 1
    rattlesnake.body_temperature = rattlesnake.ct_max
    rattlesnake.check_ct_out_of_bounds()
    assert rattlesnake.ct_out_of_bounds_tcounter == 0
    assert rattlesnake.alive is True


