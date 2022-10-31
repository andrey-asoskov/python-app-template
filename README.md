# python-app-template

Python Application Template to be tested via GHA and deployed via Docker-Compose, K8s Manifests and Helm.

## Prerequisites (Tested on)

- Python 3.9.14
- Docker 20.10.17
- Docker Compose v2.10.2
- Kubernetes server: v1.25.0
- kubectl v1.25.2
- Helm v3.10.0
- Helm Chart Testing 3.7.1

## CI/CD status

| Status |
| -------|
| ![Python-test GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Python-test.yml/badge.svg) |
| ![Docker-compose GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/DC-test.yml/badge.svg) |
| ![K8s-manifests GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/K8s-manifests.yml/badge.svg) |
| ![Helm GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Helm.yml/badge.svg) |
| ![Full-pipeline GHA Workflow](https://github.com/andrey-asoskov/python-app-template/actions/workflows/Full-pipeline.yml/badge.svg) |

## Contents

| Path               | Description                                                              |
|--------------------|--------------------------------------------------------------------------|
| .github/workflows/ | CI pipelines to test the code, build Docker image and Helm chart package |
| app/               | App code                                                                 |
| data/              | DB schema config                                                         |
| Helm/              | Helm charts config                                                       |
| K8s-manifests/     | Kubernetes manifests (an alternative to Helm charst)                     |
| tests/             | App unittests                                                            |
| .dockerignore
| .markdownlint.yaml
| .pre-commit-config.yaml
| .flake8
| .pylitrc
| .python-version
| .yamllint.yaml
| docker-compose.yaml
| Dockerfile

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

### Start the App

```commandline
# Start MySQL
docker run -d \
-v /Users/andrey-work/Documents/Work/NewJob/Stake.fish/data/datadbschema.sql:/docker-entrypoint-initdb.d/datadbschema.sql \
-p 3306:3306 \
-e MYSQL_ROOT_PASSWORD=wEAzF#5VLE \
-e MYSQL_DATABASE=db1 \
-e MYSQL_USER=dbuser \
-e MYSQL_PASSWORD=NY#xU8qfXM \
mariadb:10.9.3

# Start the app
export DB_HOST='127.0.0.1'
export DB_PORT=3306
export DB_NAME='db1'
export DB_USER='dbuser'
export DB_PASSWORD='NY#xU8qfXM'
python ./app.py

# Start via Flask CLI
export FLASK_APP=app.py
flask run \
    --host 0.0.0.0 \
    --port 3000 \
    --reload

#Via Gunicorn
gunicorn --bind 0.0.0.0:3000 --access-logfile - --error-logfile - wsgi:app
```

### Test manually

```commandline
# Root
curl -X GET  http://127.0.0.1:3000/

# Health
curl -X GET  http://127.0.0.1:3000/health 

# Metrics
curl -X GET  http://127.0.0.1:3000/metrics

# Crash
curl -X GET  http://127.0.0.1:3000/crash

# Lookup  - 1 address
curl -X GET  -H "Content-Type: application/json"  -d '{"domain":"apple.com"}'  http://127.0.0.1:3000/v1/tools/lookup 

# Lookup  - several addresses
curl -X GET  -H "Content-Type: application/json"  -d '{"domain":"cnn.com"}'  http://127.0.0.1:3000/v1/tools/lookup 

# Lookup  - bad - 1
curl -X GET  -H "Content-Type: application/json"  -d '{"domain1":"apple.com"}'  http://127.0.0.1:3000/v1/tools/lookup 

# Lookup  - bad - 2
curl -X GET  -H "Content-Type: application/json"  -d '{"domain":"444.44"}'  http://127.0.0.1:3000/v1/tools/lookup 

# Validate
curl -X POST  -H "Content-Type: application/json"  -d '{"ip":"1.2.3.4"}'  http://127.0.0.1:3000/v1/tools/validate 

# Validate - bad
curl -X POST  -H "Content-Type: application/json"  -d '{"ip":"1.2.3.444"}'  http://127.0.0.1:3000/v1/tools/validate 

# Validate - bad - IPv6
curl -X POST  -H "Content-Type: application/json"  -d '{"ip":"2001:db8::"}'  http://127.0.0.1:3000/v1/tools/validate 

# History
curl -X GET  -H "Content-Type: application/json"  http://127.0.0.1:3000/v1/history
```

### Test via Unittests

```commandline
python -m unittest tests.test.py
python -m unittest tests.test_noDB.py
```

### Create Docker image

```commandline
# Test
hadolint --config ./.hadolint.yaml Dockerfile

# Docker build
docker build -t andreyasoskovwork/app:0.1.11 -f Dockerfile . 

# Docker push
docker login -u andreyasoskovwork
docker push andreyasoskovwork/app:0.1.11
```

### Start as Docker

```commandline
#Start as docker container
docker run -d \
-p 3000:3000 \
-e DB_USER=dbuser \
-e DB_PASSWORD='NY#xU8qfXM' \
-e DB_NAME=db1 \
-e DB_PORT=3306 \
-e DB_HOST=172.17.0.2 \
andreyasoskovwork/app:0.1.11

# Start as Docker-compose
docker-compose up -d --wait --build
```

### Deploy K8s manifests

```commandline
# Start Minikube
minikube delete && minikube start --kubernetes-version=v1.25.0 \
--memory=6g --bootstrapper=kubeadm \
--driver=virtualbox \
--extra-config=kubelet.authentication-token-webhook=true \
--extra-config=kubelet.authorization-mode=Webhook \
--extra-config=scheduler.bind-address=0.0.0.0 \
--extra-config=controller-manager.bind-address=0.0.0.0

minikube delete 

# Start Kind Cluster
kind create cluster
kubectl config set-context kind-kind

kind delete cluster

# Deploy manifests
kubectl create namespace k8s-manifests
kubectl -n k8s-manifests apply -f ./K8s-manifests/1.db.yaml
kubectl -n k8s-manifests apply -f ./K8s-malnifests/2.app.yaml

# Test
kubectl -n k8s-manifests apply -f ./K8s-manifests/3.test.yaml
kubectl -n k8s-manifests get pod
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

### Test via Checkov

```commandline
checkov -d . --config-file ./.checkov.yaml
```

### Package Helm Chart

```commandline
helm package ./Helm/charts/app -d ./Helm
```

### Deploy Helm Chart

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

# App
helm install app --create-namespace --namespace helm-charts \
./Helm/charts/app --values ./Helm/app_values.yaml --wait

## Update
helm upgrade app --namespace helm-charts \
./Helm/charts/app --values ./Helm/app_values.yaml

## List
helm list --namespace helm-charts

## Test
helm test --namespace helm-charts app
kubectl -n helm-charts get pod

## Delete
helm uninstall --namespace helm-charts app
helm uninstall --namespace helm-charts db
```

### Test GHA workflows locally

```commandline
# Test using medium image
act --rm -r -W ./.github/workflows/K8s-manifests.yml  -j k8s-test -P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04

# Test using full image 20.04
act --rm -r -W ./.github/workflows/DC-test.yml -P ubuntu-22.04=catthehacker/ubuntu:full-20.04
```
