import requests
import json

def upload_score(name, score, path_to_logs):

    files = {"logfile": open(path_to_logs + '/model_logs.csv', 'rb')#,
  #           'plant_json': open(path_to_logs + '/plant.json', 'rb'),
  #           'plant_jpeg': open(path_to_logs + '/plant.jpeg', 'rb'),
             }

    requests.post(
        "https://planted.ipk-gatersleben.de/highscores/post.php",
        files=files,
        data={"name": name, "score": score},
    )


def get_scores():
    scores = json.loads(
        requests.get(
            "https://planted.ipk-gatersleben.de/highscores/highscores.json",
            headers={'Cache-Control': 'no-cache'}
        ).text
    )
    return scores

# https://planted.ipk-gatersleben.de/highscores/logs/
# https://planted.ipk-gatersleben.de/highscores/highscores.json
# clear scores and delete all log files: https://planted.ipk-gatersleben.de/highscores/clearscores.php
