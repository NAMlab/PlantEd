from __future__ import annotations

class WeatherState:
    def __init__(
            self,
            temperatur: float,
            humidity: float,
            precipitation: int,
    ) -> None:
        self.temperatur: float = temperatur
        self.humidity:float = humidity
        self.precipitation: int = precipitation

    def __str__(self):
        string = f"Temp.: {self.temperatur}, Hum.: {self.humidity}, Prec.: {self.precipitation}"
        return string

    def __eq__(self, other):

        if not isinstance(other, WeatherState):
            return False

        if self.temperatur != other.temperatur:
            return False

        if self.humidity != other.humidity:
            return False

        if self.precipitation != other.precipitation:
            return False

        return True

    def to_dict(self) -> dict:
        dic = {}

        dic["temperatur"] = self.temperatur
        dic["humidity"] = self.humidity
        dic["precipitation"] = self.precipitation

        return dic

    @classmethod
    def from_dict(cls, dic: dict) -> WeatherState:
        w_state = WeatherState(
            temperatur=dic["temperatur"],
            humidity= dic["humidity"],
            precipitation= dic["precipitation"]
        )

        return w_state
