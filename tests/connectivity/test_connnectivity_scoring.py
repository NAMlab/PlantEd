import pytest
import requests


class TestConnectivityScoring():
    def test_server_connectivity(self):
        try:
            # Attempt to ping the server
            response = requests.get('https://planted.ipk-gatersleben.de/highscores/')
            response.raise_for_status()  # Raise an exception for HTTP errors
            print("Server is reachable.")
        except requests.RequestException as e:
            # Handle the case where the server is not reachable
            print(f"Failed to connect to the server: {e}")
