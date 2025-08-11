import polars as pl

class Patch(object):
    def __init__(self, model):
        self.model = model
        self.landscape_config = model.config.Landscape_Parameters
        self.microhabitats = ['Burrow', 'Open']
        self.thermal_profile = pl.read_csv(self.landscape_config.Thermal_Database_fp)
        self.env_columns = self.landscape_config.ENV_Temperature_Cols
        self._burrow_temperature = None
        self._open_temperature = None
    
    @property
    def burrow_temperature(self):
        return self._burrow_temperature
    
    @burrow_temperature.setter
    def burrow_temperature(self, value):
        self._burrow_temperature = value
    
    @property
    def open_temperature(self):
        return self._open_temperature
    
    @open_temperature.setter
    def open_temperature(self, value):
        self._open_temperature = value
    
    def meters_to_hectares(self, val):
        return float(val / self.hectare_to_meter)
    
    def set_landscape_temperatures(self):
        # set these to env_cols
        open_temp = self.thermal_profile.select(self.env_columns.Open).row(self.model.step_id)[0]
        burrow_temp = self.thermal_profile.select(self.env_columns.Burrow).row(self.model.step_id)[0]
        self.open_temperature = open_temp
        self.burrow_temperature = burrow_temp

    def count_steps_in_one_year(self) -> int:
        self.thermal_profile = self.thermal_profile.with_columns(
            pl.col("datetime").str.to_datetime("%Y-%m-%d %H:%M:%S")
        )
        first_day = self.thermal_profile["datetime"].min()
        one_year_later = first_day + pl.duration(days=365)
        steps_count = self.thermal_profile.filter(
            (pl.col("datetime") >= first_day) & (pl.col("datetime") < one_year_later)
        ).height
        return steps_count