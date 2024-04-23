import requests
import json
import pandas as pd


def upload_score(name, score, path_to_logs, icon_name):
    files = {
        "logfile": open(path_to_logs + "/model_logs.csv", "rb")  # ,
        #           'plant_json': open(path_to_logs + '/plant.json', 'rb'),
        #           'plant_jpeg': open(path_to_logs + '/plant.jpeg', 'rb'),
    }
    try:
        response = requests.post(
            "https://planted.ipk-gatersleben.de/highscores/post.php",
            files=files,
            data={"name": name, "icon_name": icon_name, "score": score},
        )
        response.raise_for_status()
        print("score uploaded successfully")
    except requests.RequestException as e:
        print(f"Failed to upload score: {e}")


def get_scores():
    try:
        # Attempt to retrieve scores
        response = requests.get(
            "https://planted.ipk-gatersleben.de/highscores/highscores.json",
            headers={"Cache-Control": "no-cache"},
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Scores retrieved successfully!")
        return response
    except requests.RequestException as e:
        # Handle the case where the retrieval fails
        print(f"Failed to retrieve scores: {e}")
        return None


def get_csv(id):
    csv = f"https://planted.ipk-gatersleben.de/highscores/logs/{id}.csv"
    if csv is not None:
        return pd.read_csv(csv)
    else:
        return None


# https://planted.ipk-gatersleben.de/highscores/logs/
# https://planted.ipk-gatersleben.de/highscores/highscores.json
# clear scores and delete all log files: https://planted.ipk-gatersleben.de/highscores/clearscores.php
