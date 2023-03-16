import requests
import json


def upload_score(name, score):
    test_file = open("logfile.csv", "rb")
    requests.post(
        "http://biotools-online.com/planted-highscore/post.php",
        files={"logfile": test_file},
        data={"name": name, "score": score},
    )


def get_scores():
    scores = json.loads(
        requests.get(
            "http://biotools-online.com/planted-highscore/highscores.json"
        ).text
    )
    return scores


# https://biotools-online.com/planted-highscore/logs/1.csv
# http://biotools-online.com/planted-highscore/highscores.json
# clear scores: http://biotools-online.com/planted-highscore/clearscores.php
