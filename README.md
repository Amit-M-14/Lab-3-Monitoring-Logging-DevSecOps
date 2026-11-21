# Lab 3: DevOps Automation, Observability and DevSecOps

**Student:** Amit Mohanty  |  **Roll No.:** 2301730325

This lab covers infrastructure automation, infrastructure as code, centralized logging, DevSecOps, monitoring, testing, and a final consolidated report. Everything runs locally on one Windows machine using WSL2, Docker Desktop and Jenkins, with no cloud account needed.

## Task overview and status

| # | Task | Marks | Tools | Status |
|---|------|-------|-------|--------|
| 1 | Configure infrastructure and automate application configuration | 5 | Ansible | Done, report written |
| 2 | Provision scalable infrastructure (Infrastructure as Code) | 5 | Terraform, Docker provider | Steps ready, evidence pending |
| 3 | Implement centralized logging | 5 | Elasticsearch, Logstash, Kibana | Not finished (image download failed, see Task 3) |
| 4 | Integrate security into the CI/CD pipeline | 5 | Jenkins, pip-audit, Bandit, detect-secrets | Steps ready, pipeline not yet run |
| 5 | Set up monitoring | 5 | Prometheus, Grafana | Planned |
| 6 | Feature flags, load testing, Selenium testing | 5 | Python, Locust, Selenium | Planned |
| 7 | Monitoring, logging and DevSecOps report | 10 | Word report built from tasks 1 to 6 | After tasks 1 to 6 |

## Environment

- Windows with **WSL2** running **Ubuntu 26.04 LTS** (Ansible, Terraform and the scanners run here)
- **Docker Desktop** with WSL integration enabled for Ubuntu
- **Jenkins** at `http://localhost:8080` (from Lab 2)
- **VS Code** for editing

Prerequisites: Ubuntu under WSL2, Docker Desktop running, and Jenkins running.

## Folder structure

```
Lab 3/
├── README.md
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
│   ├── requirements.txt
│   └── insecure_demo.py        (deliberately insecure, deleted after build #1)
├── prometheus/                 (Task 5, planned)
└── testing/                    (Task 6, planned)
```

Windows paths are reachable from Ubuntu under `/mnt/c/`. Quote any path that contains spaces:

```bash
cd "/mnt/c/Users/Amit/Desktop/devops stuff/Lab 3"
```

---

## Task 1: Ansible

**Goal:** write an inventory and a playbook that configure a target node and apply them.

**What it does:** the playbook installs nginx, curl and git, creates `/var/www/ansible-app`, renders a Jinja2 template into `index.html`, configures nginx to serve it on port **8088**, and ensures the service is running. A handler restarts nginx only when its configuration changes.

**Target node:** `node1`, the local Ubuntu machine (`ansible_connection=local`).

```bash
cd "/mnt/c/Users/Amit/Desktop/devops stuff/Lab 3/ansible"
ansible all -i inventory.ini -m ping
ansible-playbook -i inventory.ini site.yml --syntax-check
ansible-playbook -i inventory.ini site.yml
curl http://localhost:8088
ansible-playbook -i inventory.ini site.yml     # second run proves idempotency
```

**Result:** first run `ok=7 changed=5 failed=0`. Second run `ok=6 changed=0 failed=0`. The page at port 8088 shows "Deployed by Ansible".

**Notes:**
- `ansible.cfg` is ignored when the project sits on a Windows drive (`/mnt/c`), so the inventory is passed with `-i inventory.ini`.
- A dry run with `--check` fails at the nginx service task, because nginx is not installed in check mode. This is expected, not a playbook error.
- Ansible needs sudo without a prompt. For this lab only, passwordless sudo was enabled for the lab user. Do not do this on a real system.

**Report:** `Task_1_Ansible_Configuration_Automation_Amit_Mohanty.docx`

---

## Task 2: Terraform

**Goal:** provision scalable infrastructure with configuration files, then initialize, plan and apply.

**What it does:** uses the `kreuzwerker/docker` provider to run a set of `nginx:alpine` containers. `instance_count` (default 2) controls how many, and `base_port` (default 9081) sets the first host port, so containers are reachable on 9081, 9082 and so on.

```bash
cd "/mnt/c/Users/Amit/Desktop/devops stuff/Lab 3/terraform"
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply -auto-approve
docker ps --filter name=tf-web
curl http://localhost:9081
terraform state list

terraform apply -auto-approve -var="instance_count=4"    # scale up to 4
terraform output
terraform apply -auto-approve -var="instance_count=2"    # scale back down
terraform destroy -auto-approve                          # clean up
```

**Expected:** `Plan: 3 to add` first (one image, two containers), then `2 to add` when scaling to 4.

---

## Task 3: Centralized logging (ELK)

**Goal:** collect, parse and visualize logs with the ELK stack.

**Design:**

```
nginx (access.log) → shared volume → Logstash (grok) → Elasticsearch → Kibana
        ↑
   traffic generator (requests a mix of 200, 301, 404 and 500 responses)
```

| Service | Port |
|---------|------|
| Elasticsearch | 9200 |
| Kibana | 5601 |
| nginx | 8085 (not 8080, which Jenkins uses) |

Logstash parses each line with the `COMBINEDAPACHELOG` grok pattern into fields such as `clientip`, `verb`, `request`, `response` and `bytes`, and writes to the index `nginx-logs-YYYY.MM.dd`.

```bash
sudo sysctl -w vm.max_map_count=262144      # required by Elasticsearch; resets when WSL restarts
cd "/mnt/c/Users/Amit/Desktop/devops stuff/Lab 3/elk"
docker compose up -d
docker compose ps
curl http://localhost:9200
docker exec nginx-web tail -n 6 /logs/access.log
docker logs logstash --tail 40
curl "http://localhost:9200/_cat/indices?v"
docker compose down
```

In Kibana (`http://localhost:5601`): create a data view `nginx-logs-*` with `@timestamp`, explore it in Discover, filter with `response : 404`, and build a dashboard named **Nginx Log Monitoring** (requests over time by status, status share, top requested paths).

**Status:** not finished. The three Elastic images total about 1.5 GB, and the pull failed repeatedly on a slow, unstable connection, ending in DNS errors. Options for finishing it: pull the images once on a faster network, or use an Elastic Cloud trial and upload the log file in Kibana. The Cloud route has no Logstash, so it would need a note in the report.

---

## Task 4: DevSecOps

**Goal:** add vulnerability, code and secret scanning to a CI/CD pipeline and show secure pipeline practices.

**Scanners:**

| Check | Tool | Finds |
|-------|------|-------|
| Dependency scan | pip-audit | Known vulnerabilities in pinned packages |
| Static analysis | Bandit | Insecure code (`shell=True`, weak MD5 hashing, binding to 0.0.0.0) |
| Secret scan | detect-secrets | Hard-coded passwords and API keys |

**Demo setup:** `requirements.txt` pins old, vulnerable versions, and `insecure_demo.py` contains a hard-coded password and API key, an MD5 hash and a `shell=True` call. These are deliberate, so the scanners have something to find.

**Manual scans (Ubuntu):**

```bash
cd "/mnt/c/Users/Amit/Desktop/devops stuff/Lab 3/devsecops"
python3 -m venv ~/devsecops-venv
source ~/devsecops-venv/bin/activate
pip install pip-audit bandit detect-secrets
pip-audit --no-deps --disable-pip -r requirements.txt
bandit -r .
detect-secrets-hook *.py
```

**Jenkins pipeline `devsecops-pipeline`:** stages Secret Scan, Dependency Scan, Static Analysis, Build Image, Secure Credentials.

Secure practices demonstrated:
- The scans run inside `python:3.11-slim` containers with the project mounted read-only.
- The scans are gates. The image is built only if all of them pass.
- The API key comes from the Jenkins credential store (ID `demo-api-key`), not from code, and Jenkins masks it in the log.

**Flow:** build #1 fails on purpose, showing the gates blocking insecure code. Then delete `insecure_demo.py`, regenerate `requirements.txt` with current versions, and run build #2, which passes. Optionally scan the built image with Trivy (`aquasec/trivy`).

---

## Task 5: Monitoring with Prometheus and Grafana (planned)

Run Prometheus and Grafana with Docker Compose. Prometheus scrapes metrics from a target application or system, and Grafana visualizes them through a Prometheus data source on dashboards. Files will go in `prometheus/`. Details will be added once the task is done.

## Task 6: Feature flags, load testing and Selenium (planned)

Implement a feature flag in a small Python app, run a load test with Locust, and automate a browser check with Selenium. Commands, configuration, screenshots and observations will be recorded. Files will go in `testing/`. Details will be added once the task is done.

## Task 7: Monitoring, logging and DevSecOps report (planned)

A Word report (10 marks) describing the automation, observability setup, security findings and observations, with screenshots from tasks 1 to 6. It follows the same format as the earlier lab reports: a header table, numbered sections with commands and evidence, then observations and a conclusion.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Docker pulls fail with DNS or "i/o timeout" | `wsl --shutdown` in PowerShell, restart Docker Desktop, retry. If it persists, set `"dns": ["8.8.8.8", "1.1.1.1"]` in Docker Desktop, Settings, Docker Engine. Disable any VPN. |
| Elasticsearch container exits (code 137 or max_map_count error) | Rerun `sudo sysctl -w vm.max_map_count=262144`. For out-of-memory, add `[wsl2]` with `memory=6GB` to `C:\Users\Amit\.wslconfig`, then `wsl --shutdown`. |
| Ansible reports "Timed out waiting for become" | Enable passwordless sudo for the lab user, or enter the password with `-K`. |
| `docker` not found in Ubuntu | Docker Desktop, Settings, Resources, WSL Integration, enable Ubuntu. |
| Port already in use | Change the host port (`base_port` in Terraform, or the left side of the port mapping in Compose). |
| A path with spaces fails | Wrap it in double quotes. |
