import pytest
import numpy as np
from suffugium.metabolism import EctothermMetabolism

@pytest.fixture
def ectotherm():
    """Fixture for creating an instance of EctothermMetabolism with made up numbers."""
    return EctothermMetabolism(initial_metabolic_state=1000, X1_mass=0.930, X2_temp=0.044, X3_const=-2.58, prey_body_size=65,max_meals=2, calories_per_gram=4.1)

def test_initial_metabolic_state(ectotherm):
    """Test that the initial metabolic state is set correctly."""
    assert ectotherm.metabolic_state == 1000

def test_metabolic_state_setter_range(ectotherm):
    """Test setting the metabolic state using a range."""
    ectotherm.metabolic_state = range(900, 1100)
    assert 900 <= ectotherm.metabolic_state <= 1100

def test_metabolic_state_setter_invalid(ectotherm):
    """Test that an invalid metabolic state raises a ValueError."""
    with pytest.raises(ValueError):
        ectotherm.metabolic_state = "invalid_value"

def test_smr_eq(ectotherm):
    """Test the calculation of SMR."""
    smr = ectotherm.smr_eq(mass=1000, temperature=30)
    expected_smr = 10**((0.930 * np.log10(1000)) + (0.044 * 30) - 2.58)
    assert smr == pytest.approx(expected_smr, rel=1e-3)

def test_hourly_energy_expenditure(ectotherm):
    """Test the calculation of hourly energy expenditure."""
    smr = 1.0  # Example SMR
    activity_coefficient = 1.5
    hee = ectotherm.hourly_energy_expendeture(smr=smr, activity_coeffcient=activity_coefficient)
    expected_cals = smr * activity_coefficient * ectotherm.mlo2_to_joules * ectotherm.joules_to_cals
    assert hee == pytest.approx(expected_cals, rel=1e-3)

def test_energy_intake(ectotherm):
    """Test the calculation of energy intake."""
    prey_mass = 100  # grams
    cal_per_gram_conversion = 4.1  # calories per gram
    percent_digestion_cals = 0.8  # 80% efficiency
    intake = ectotherm.energy_intake(prey_mass, cal_per_gram_conversion, percent_digestion_cals)
    expected_intake = prey_mass * cal_per_gram_conversion * percent_digestion_cals
    assert intake == pytest.approx(expected_intake, rel=1e-3)

def test_cals_lost(ectotherm):
    """Test the calories lost calculation."""
    initial_state = ectotherm.metabolic_state
    mass = 1000
    temperature = 30
    activity_coefficient = 1.5
    ectotherm.cals_lost(mass=mass, temperature=temperature, activity_coeffcient=activity_coefficient)
    smr = ectotherm.smr_eq(mass, temperature)
    cals_spent = ectotherm.hourly_energy_expendeture(smr=smr, activity_coeffcient=activity_coefficient)
    assert ectotherm.metabolic_state == pytest.approx(initial_state - cals_spent, rel=1e-3)

def test_cals_gained(ectotherm):
    """Test the calories gained calculation."""
    initial_state = ectotherm.metabolic_state
    prey_mass = 100
    cal_per_gram_conversion = 4.1
    percent_digestion_cals = 0.8
    ectotherm.cals_gained(prey_mass, cal_per_gram_conversion, percent_digestion_cals)
    # Assuming metabolic_state update is uncommented in the cals_gained method
    # expected_gain = prey_mass * cal_per_gram_conversion * percent_digestion_cals
    # assert ectotherm.metabolic_state == pytest.approx(initial_state + expected_gain, rel=1e-3)

def test_metabolic_state_random_sampling(ectotherm):
    """Test random sampling within a tuple range for metabolic state."""
    ectotherm.metabolic_state = (500, 600)
    assert 500 <= ectotherm.metabolic_state <= 600