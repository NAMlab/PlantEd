import random
import math

# Constants
BASE_TEMP = 15  # Base temperature in °C
TEMP_AMPLITUDE = 15  # Maximum temperature deviation from base in °C
SOLAR_CONSTANT = 1367  # W/m^2
LATITUDE = 51.17  # Latitude of location in degrees
DECLINATION = 23.44  # Declination angle in degrees

# Seasonal temperature model based on sinusoidal function
def seasonal_temperature(time_in_hours, latitude, declination, solar_constant):
    time_in_days = time_in_hours / 24
    seasonal_factor = math.sin(2 * math.pi * (time_in_days - 93) / 365)
    solar_angle = math.acos(-math.tan(math.radians(latitude)) * math.tan(math.radians(declination)))
    if solar_angle < 0 or solar_angle > math.pi:
        solar_angle = 0
    solar_radiation = solar_constant * math.cos(solar_angle)
    temperature = BASE_TEMP + TEMP_AMPLITUDE * seasonal_factor + solar_radiation / (60 * 60 * 24)
    return temperature

# Humidity model based on relative humidity data
def humidity(temperature, time_of_day):
    if time_of_day >= 6 and time_of_day < 18:
        relative_humidity = random.uniform(30, 60)
    elif time_of_day >= 18 or time_of_day < 6:
        relative_humidity = random.uniform(60, 80)
    else:
        raise ValueError("Invalid time of day")
    saturation_vapor_pressure = 6.11 * math.exp(17.67 * temperature / (temperature + 243.5))
    actual_vapor_pressure = relative_humidity * saturation_vapor_pressure / 100
    return relative_humidity, actual_vapor_pressure

# Main function for weather simulation
def simulate_weather(time_in_hours, time_of_day):
    temperature = seasonal_temperature(time_in_hours, LATITUDE, DECLINATION, SOLAR_CONSTANT)
    relative_humidity, vapor_pressure = humidity(temperature, time_of_day)
    return temperature, relative_humidity

# Example usage
time_in_hours = 24 * 150 + 12
time_of_day = 12
for i in range(24):
    time_of_day = i
    time_in_hours = 25*110+i
    temperature, relative_humidity = simulate_weather(time_in_hours, time_of_day)
    print(f"Time: {time_of_day} Temperature: {temperature}°C, Relative Humidity: {relative_humidity}%")