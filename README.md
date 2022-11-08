# python-app-template

Python Flask Application Template to be tested via GHA and deployed via Docker-Compose, K8s Manifests and Helm.

## Prerequisites (Tested on)

- Python 3.9.14
- Docker 20.10.17
- Docker Compose v2.10.2
- Haskell Dockerfile Linter 2.10.0
- Container-structure-test 1.11.0
- Kubernetes server: v1.25.0
- kubectl v1.25.2
- Helm v3.10.0
- Helm Chart Testing 3.7.1
- Checkov 2.1.270
- Act 0.2.32

## CI/CD status

| Status |
| -------|
| ![Python-test GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Python-test.yml/badge.svg) |
| ![Docker-compose GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/DC-test.yml/badge.svg) |
| ![K8s-manifests GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/K8s-manifests.yml/badge.svg) |
| ![Helm GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Helm.yml/badge.svg) |
| ![Full-pipeline GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Full-pipeline.yml/badge.svg) |

## Contents

| Path                    | Description                                                                      |
|-------------------------|----------------------------------------------------------------------------------|
| .github/workflows/      | CI pipelines to test app, build Docker image, test Docker-compose config, K8s manifests and test & package Helm chart |
| app/                    | App for API with Prometheus client and migrations                                |
| cs-test/                | Container Structure Test config to test Docker image                             |
| data/                   | DB secrets                                                                       |
| Helm/                   | Helm chart with test and migration hooks                                         |
| K8s-kind/               | Kubernetes Kind cluster config                                                   |
| K8s-manifests/          | Kubernetes manifests (an alternative to Helm charts)                             |
| tests/                  | App unittests                                                                    |
| .checkov.yaml
| .dockerignore
| .flake8
| .hadolint.yaml          |  Hadlint config to test Dockerfile
| .markdownlint.yaml
| .pre-commit-config.yaml | Pre-commit hooks to test the code
| .pylitrc
| .python-version
| .yamllint.yaml
| docker-compose.yaml     | Docker-compose file
| Dockerfile              | Docker File

## Usage

### Test Python Code

```commandline
# Format
python -m pip install -r ./tests/requirements.txt
flake8 ./tests/*.py 
flake8 ./app/*.py 

# Lint
pylint --rcfile ./.pylintrc ./tests/*.py 
pylint --rcfile ./.pylintrc ./app/*.py 
```

### Test via Unittests

```commandline
python -m unittest tests.test
python -m unittest tests.test_noDB
```

### Start the App

```commandline
# Start MariaDB
docker run -d \
-v $(pwd)/data/mysql-root-password:/run/secrets/mysql-root-password \
-v $(pwd)/data/mysql-user-name:/run/secrets/mysql-user-name \
-v $(pwd)/data/mysql-user-password:/run/secrets/mysql-user-password \
-v $(pwd)/data/mysql-conf-file:/run/secrets/mysql-conf-file \
-p 3306:3306 \
-e MYSQL_ROOT_PASSWORD_FILE=/run/secrets/mysql-root-password \
-e MYSQL_DATABASE=db1 \
-e MYSQL_USER_FILE=/run/secrets/mysql-user-name \
-e MYSQL_PASSWORD_FILE=/run/secrets/mysql-user-password \
--health-cmd="mysql --defaults-extra-file=/run/secrets/mysql-conf-file -e 'SHOW databases;'" \
mariadb:10.9.3

# Start the app
export DB_HOST='127.0.0.1'
export DB_PORT=3306
export DB_NAME='db1'
python ./app.py

# Start via Flask CLI
export FLASK_APP=app.py
flask run \
    --host 0.0.0.0 \
    --port 3000 \
    --reload

# Start via Gunicorn
gunicorn --bind 0.0.0.0:3000 --access-logfile - --error-logfile - wsgi:app
```

### Run DB migrations

```commandline
# Create migration script after Schema Change
flask db migrate -m "migration1"

# Do the migration
flask db upgrade
```

### Test manually

```commandline
# Create
curl -X GET  http://127.0.0.1:3000/create

# Root
curl -X GET  http://127.0.0.1:3000/

# Health
curl -X GET  http://127.0.0.1:3000/health 

# Metrics
curl -X GET  http://127.0.0.1:3000/metrics

# Crash
curl -X GET  http://127.0.0.1:3000/crash
```

### Test config (Dockerfile, k8s manifests, Helm, GHA) via Checkov

```commandline
checkov -d . --config-file ./.checkov.yaml
```

### Create Docker image

```commandline
# Test
hadolint --config ./.hadolint.yaml Dockerfile

# Docker build
docker build -t andreyasoskovwork/cat-app:0.1.15 -f Dockerfile . 

# Docker push
docker login -u andreyasoskovwork
docker push andreyasoskovwork/cat-app:0.1.15

# Test 
container-structure-test test --image andreyasoskovwork/cat-app:0.1.14 --config ./cs-test/config.yaml
```

### Start as Docker

```commandline
# Start as docker container
docker run -d \
-v $(pwd)/data/mysql-user-name:/run/secrets/mysql-user-name \
-v $(pwd)/data/mysql-user-password:/run/secrets/mysql-user-password \
-p 3000:3000 \
-e DB_NAME=db1 \
-e DB_PORT=3306 \
-e DB_HOST=172.17.0.2 \
andreyasoskovwork/cat-app:0.1.14

# Test docker-compose
docker-compose -f docker-compose.yaml config

# Start as Docker-compose
docker-compose up -d --wait --build
```

### Start local Kubernetes cluster

```commandline
# Start Kind Cluster
kind create cluster --config ./K8s-kind/kind-config.yaml

# Create Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Delete Kind Cluster
kind delete cluster
```

### Deplpoy via K8s manifests

```commandline
# Test manifests
kubectl apply --validate --dry-run=client -f ./K8s-manifests/1.db.yaml
kubectl apply --validate --dry-run=client -f ./K8s-manifests/2.app.yaml
kubectl apply --validate --dry-run=client -f ./K8s-manifests/3.test.yaml

kubectl apply  --dry-run=client -f ./K8s-manifests/1.db.yaml-o yaml
kubectl apply  --dry-run=client -f ./K8s-manifests/2.app.yaml -o yaml
kubectl apply  --dry-run=client -f ./K8s-manifests/3.test.yaml -o yaml

# Deploy manifests
kubectl create namespace k8s-manifests
kubectl -n k8s-manifests apply -f ./K8s-manifests/1.db.yaml
kubectl -n k8s-manifests apply -f ./K8s-manifests/2.app.yaml

# Test
kubectl -n k8s-manifests apply -f ./K8s-manifests/3.test.yaml
kubectl -n k8s-manifests get pod

# Test Nginx Ingress
curl --resolve www.example.com:80:127.0.0.1 -H 'Host: www.example.com' localhost/health
```

### Test Helm Chart

```commandline
# Test Chart
ct lint --config ./Helm/ct-lint.yaml \
--charts ./Helm/charts/app

helm lint ./Helm/charts/app

helm template --namespace helm-charts app \
./Helm/charts/app --values ./Helm/app_values.yaml \
--validate  

helm install --namespace helm-charts app \
./Helm/charts/app --values ./Helm/app_values.yaml \
--dry-run
```

### Deploy via Helm Chart

```commandline
# DB
helm repo add bitnami https://charts.bitnami.com/bitnami

helm template --namespace helm-charts db \
bitnami/mariadb --version 11.3.3 --values ./Helm/mariadb_values.yaml \
--validate

helm install --namespace helm-charts db \
bitnami/mariadb --version 11.3.3 --values ./Helm/mariadb_values.yaml \
--dry-run 

helm install --create-namespace --namespace helm-charts db \
bitnami/mariadb --version 11.3.3 --values ./Helm/mariadb_values.yaml \
--wait

helm upgrade --namespace helm-charts db \
bitnami/mariadb --version 11.3.3 --values ./Helm/mariadb_values.yaml \
--wait

# App
helm install app --create-namespace --namespace helm-charts \
./Helm/charts/app --values ./Helm/app_values.yaml --wait

## Update with DB migration
helm upgrade app --namespace helm-charts \
./Helm/charts/app --values ./Helm/app_values.yaml

## List
helm list --namespace helm-charts

## Test
helm test --namespace helm-charts app
kubectl -n helm-charts get pod

# Test Nginx Ingress
curl --resolve www.example.com:80:127.0.0.1 -H 'Host: www.example.com' localhost/health

## Delete
helm uninstall --namespace helm-charts app
helm uninstall --namespace helm-charts db
kubectl delete namespace helm-charts
```

### Package Helm Chart

```commandline
helm package ./Helm/charts/app -d ./Helm
```

### Get the data from App API

```commandline
## Via Docker or local 
# Create data
curl http://127.0.0.1:3000/create

# Query the data
curl http://127.0.0.1:3000 | jq .

# Query prometheus Metrics
curl http://127.0.0.1:3000/metrics

## Via K8s Ingress
# Create data
curl --resolve www.example.com:80:127.0.0.1 -H 'Host: www.example.com' http://127.0.0.1/create

# Query the data
curl --resolve www.example.com:80:127.0.0.1 -H 'Host: www.example.com' http://127.0.0.1 | jq .

# Query prometheus Metrics
curl --resolve www.example.com:80:127.0.0.1 -H 'Host: www.example.com'  http://127.0.0.1/metrics
```

### Test GHA workflows locally

```commandline
# Test using medium image
act --rm -r -W ./.github/workflows/Python-test.yml -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04

# Test using full image 20.04
act --rm -r -W ./.github/workflows/Python-test.yml -P ubuntu-22.04=catthehacker/ubuntu:full-20.04
```
