#!/usr/bin/env bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# license         :GPLv3
# ==============================================================================

# For help
# - https://scotch.io/tutorials/google-cloud-platform-i-deploy-a-docker-app-to-google-container-engine-with-kubernetes
# Kubernetes: https://kubernetes.io/docs/user-guide/kubectl
# - https://medium.com/bitnami-perspectives/jupyter-notebooks-for-kubernetes-via-google-summer-of-code-dfdc6e413b8a
# - Persistent Storage: http://spr.com/configuring-persistence-storage-docker-kubernetes/

## gcloud SDK

# Configure gcloud
gcloud init

# See gcloud configuration
gcloud config list
gcloud components list

# Install/Update gcloud components if necessary
# gcloud components install kubectl
# gcloud components update

#  Set default project
gcloud config set project ee-deforestprob

## Permanent disk
# gcloud compute disks create --size 250GB deforestprob-disk

## Cluster

# Create cluster
gcloud container clusters create deforestprob-cluster

# Created [https://container.googleapis.com/v1/projects/ee-deforestprob/zones/europe-west1-d/clusters/deforestprob-cluster].
# kubeconfig entry generated for deforestprob-cluster.
# NAME                  ZONE            MASTER_VERSION  MASTER_IP     MACHINE_TYPE   NODE_VERSION  NUM_NODES  STATUS
# deforestprob-cluster  europe-west1-d  1.6.7           35.195.74.48  n1-standard-1  1.6.7         3          RUNNING

# Set it as the default cluster
gcloud config set container/cluster deforestprob-cluster
gcloud config list

# Getting the cluster credentials
gcloud container clusters get-credentials deforestprob-cluster --zone europe-west1-d --project ee-deforestprob

# Start a proxy to connect to Kubernetes control panel with browser 
# kubectl proxy

# Open the Dashboard interface by navigating to the following location in the browser: http://127.0.0.1:8001/ui

## Deploy Docker image
kubectl run deforestprob-dep --image=ghislainv/docker-debian-jupyter --port=8888

# Get Deployment and created pods
kubectl get deployments  # -w # Uncomment -w if you want to see how it is created
kubectl get pods  # -w

## Services
kubectl create -f gke/service.yml
kubectl get services

## Delete container
gcloud container clusters delete deforestprob-cluster --async
