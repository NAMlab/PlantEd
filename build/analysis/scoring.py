import requests
import json


def upload_score(name, score):
    requests.get("http://biotools-online.com/planted-highscore/post.php?name=" + name + "&score=" + str(score))

def get_scores():
    scores = json.loads(requests.get("http://biotools-online.com/planted-highscore/highscores.json").text)
    return(scores)