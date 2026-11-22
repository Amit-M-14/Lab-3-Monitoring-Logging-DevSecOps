import json
from flask import Flask
app = Flask(__name__)

def flag(name):
    with open("flags.json") as f:
        return json.load(f).get(name, False)

@app.route("/")
def home():
    if flag("new_homepage"):
        return "<h1 id='title'>New Homepage</h1>"
    return "<h1 id='title'>Old Homepage</h1>"

@app.route("/flags")
def flags():
    with open("flags.json") as f:
        return f.read()

app.run(host="0.0.0.0", port=8080)
