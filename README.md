# DevOps Automation Lab 3

**Student:** Amit Mohanty  
**Roll No.:** 2301730325

Hands-on DevOps lab covering configuration management, infrastructure as code, centralized logging, DevSecOps, monitoring, and feature flags with load and browser testing. Each task has its own folder and a written report with screenshots.

## Tasks

| # | Task | Tool(s) | Folder | Report |
|---|------|---------|--------|--------|
| 1 | Configure infrastructure and automate application configuration | Ansible | [`ansible/`](ansible/) | `Task_1_Ansible_Configuration_Automation_Amit_Mohanty.pdf` |
| 2 | Provision and scale Docker containers | Terraform (Docker provider) | [`terraform/`](terraform/) | `Task_2_Terraform_Docker_Amit_Mohanty.pdf` |
| 3 | Centralized logging | Elasticsearch, Logstash, Kibana | [`elk/`](elk/) | `Task_3_ELK_Centralized_Logging_Amit_Mohanty.pdf` |
| 4 | Security in the CI/CD pipeline | pip-audit, Bandit, detect-secrets, Jenkins | [`devsecops/`](devsecops/) | `Task_4_DevSecOps_Pipeline_Amit_Mohanty.pdf` |
| 5 | Application and host monitoring | Prometheus, Grafana, node-exporter | [`prometheus/`](prometheus/) | `Task_5_Prometheus_Grafana_Amit_Mohanty.pdf` |
| 6 | Feature flags, load testing, automated browser testing | Flask, Apache Bench, Selenium | [`feature-flags/`](feature-flags/) | `Task_6_Feature_Flags_Load_Selenium_Amit_Mohanty.pdf` |
| 7 | Monitoring, logging and DevSecOps report | n/a | n/a | `Task_7_Monitoring_Logging_DevSecOps_Report_Amit_Mohanty.pdf` |

## Repository layout

```
Lab 3/
├── ansible/
│   ├── inventory.ini
│   ├── site.yml
│   └── templates/index.html.j2
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── elk/
│   ├── docker-compose.yml
│   ├── logstash/pipeline/logstash.conf
│   └── nginx/default.conf
├── devsecops/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── prometheus/
│   └── docker-compose.yml        (plus the Prometheus configuration and the monitored app)
├── feature-flags/
│   ├── app.py
│   ├── flags.json
│   └── test_flag.py
└── reports/                      (the seven PDF reports)
```

## Environment

- Windows with **Ubuntu 26.04 LTS on WSL2**
- **Docker Desktop** with Docker Compose
- Ansible (ansible-core 2.20.1), Terraform v1.17.2, Python 3 with `venv`, Apache Bench 2.3
- Jenkins 2.568.2 (Windows) for the DevSecOps pipeline

All commands below are run from the Ubuntu (WSL2) terminal inside the matching folder.

## Ports used

| Service | Port |
|---------|------|
| Ansible-managed nginx | 8088 |
| Terraform nginx containers | 9081, 9082 (up to 9084 when scaled to 4) |
| ELK: nginx web, Elasticsearch, Kibana | 8085, 9200, 5601 |
| Monitored app, node-exporter, Prometheus, Grafana | 5055, 9100, 9090, 3000 |
| Feature-flag app, Selenium Grid | 5060, 4444 |
| Jenkins | 8080 |

## How to run each task

### Task 1: Ansible

```bash
sudo apt update && sudo apt install -y ansible
cd ansible
ansible all -i inventory.ini -m ping
ansible-playbook -i inventory.ini site.yml --syntax-check
ansible-playbook -i inventory.ini site.yml
curl http://localhost:8088
```

Run the playbook a second time to confirm idempotency (`changed=0`).

### Task 2: Terraform

```bash
cd terraform
terraform init
terraform fmt && terraform validate
terraform plan
terraform apply
docker ps --filter name=tf-web
```

Scale by changing `instance_count` in `variables.tf` (default 2) and applying again.

### Task 3: ELK stack

```bash
cd elk
sudo sysctl -w vm.max_map_count=262144
docker compose up -d
```

Open Kibana at <http://localhost:5601>, create a data view for `nginx-logs-*` with `@timestamp`, then use Discover (for example `response : 404`) and the Nginx Log Monitoring dashboard.

### Task 4: DevSecOps

Run the scanners manually:

```bash
cd devsecops
python3 -m venv ~/devsecops-venv && source ~/devsecops-venv/bin/activate
pip install pip-audit bandit detect-secrets
pip-audit --no-deps --disable-pip -r requirements.txt
bandit -r . -lll
detect-secrets-hook *.py
```

The Jenkins pipeline `devsecops-pipeline` runs the same three scans as gates (Secret Scan, Dependency Scan, Static Analysis), then Build Image and Secure Credentials only if every scan passes. The API key is kept in the Jenkins credential store as secret text with the ID `demo-api-key`, so no secret is stored in this repository. Docker Desktop must be running before the pipeline starts.

### Task 5: Prometheus and Grafana

```bash
cd prometheus
docker compose up -d
docker compose ps
```

- Prometheus targets: <http://localhost:9090/targets>
- Grafana: <http://localhost:3000> (add Prometheus as the data source)
- App metrics: <http://localhost:5055/metrics>

Queries used:

```
sum by (endpoint) (rate(app_requests_total[1m]))
histogram_quantile(0.95, sum by (le, endpoint) (rate(app_request_latency_seconds_bucket[1m])))
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)
```

### Task 6: Feature flags, load and Selenium tests

```bash
cd feature-flags
python3 -m venv venv && source venv/bin/activate
pip install flask selenium
python app.py                      # serves on port 5060
ab -n 2000 -c 50 http://localhost:5060/
```

For the Selenium test, run the app and a Chrome container on one Docker network:

```bash
docker network create flagnet
docker run -d --name flagapp --network flagnet -p 5060:8080 \
  -v "$PWD":/app -w /app python:3.11-slim sh -c "pip install -q flask && python app.py"
docker run -d --name selenium --network flagnet -p 4444:4444 \
  --shm-size=2g selenium/standalone-chrome

export APP_URL=http://flagapp:8080/
echo '{"new_homepage": true}'  > flags.json && python test_flag.py "New Homepage"
echo '{"new_homepage": false}' > flags.json && python test_flag.py "Old Homepage"
```

The flag is read from `flags.json` on every request, so changing it switches the homepage without a restart.

## Key results

- **Ansible:** first run `ok=7 changed=5 failed=0`; second run `changed=0`.
- **Terraform:** plan of 3 resources; scaled from 2 to 4 containers and back to 2.
- **ELK:** more than 104 thousand nginx events parsed and indexed; `response : 404` isolated 2,716 events in one hour.
- **DevSecOps:** 2 HIGH Bandit findings and 2 hard-coded secret locations found, then clean rescans; Jenkins build #6 passed all five stages with the credential masked.
- **Monitoring:** all 3 Prometheus targets UP; dashboards for request rate, P95 latency, CPU and memory.
- **Feature flags:** 2000 requests with 0 failures in both load runs; both Selenium checks passed.

## Cleanup

```bash
cd terraform && terraform destroy
cd ../elk && docker compose down -v
cd ../prometheus && docker compose down
docker rm -f flagapp selenium && docker network rm flagnet
```

## Notes

- The Flask development server was used for all demos and load tests, so throughput figures are relative, not production capacity.
- `devsecops/insecure_demo.py` was a deliberate vulnerable file and was deleted during remediation. If it is ever recreated, do not commit it.
- Add `venv/`, `.terraform/` and `*.tfstate*` to `.gitignore`.