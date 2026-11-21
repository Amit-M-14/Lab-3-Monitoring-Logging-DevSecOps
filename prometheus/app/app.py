import time
import random
from flask import Flask, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUESTS = Counter("app_requests_total", "Total requests", ["endpoint", "status"])
LATENCY = Histogram("app_request_latency_seconds", "Request latency", ["endpoint"])


@app.route("/")
def home():
    with LATENCY.labels("/").time():
        time.sleep(random.uniform(0.01, 0.1))
        REQUESTS.labels("/", "200").inc()
        return "Hello from the monitored app"


@app.route("/slow")
def slow():
    with LATENCY.labels("/slow").time():
        time.sleep(random.uniform(0.3, 0.8))
        REQUESTS.labels("/slow", "200").inc()
        return "Slow endpoint"


@app.route("/error")
def error():
    REQUESTS.labels("/error", "500").inc()
    return "Simulated error", 500


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
