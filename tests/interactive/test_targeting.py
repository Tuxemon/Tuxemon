"""
Simple test to test that targets are sorted correctly
after being loaded from the json db files.
"""
import json


data = """{
  "target": {
    "enemy monster": 2,
    "enemy team": 0,
    "enemy trainer": 0,
    "own monster": 1,
    "own team": 0,
    "own trainer": 0,
    "item": 0
  }
}"""

data = json.loads(data)

from operator import itemgetter
target = map(itemgetter(0), filter(itemgetter(1), sorted(data["target"].items(), key=itemgetter(1), reverse=True)))
print(target)
