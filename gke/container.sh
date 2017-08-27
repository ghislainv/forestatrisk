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

# gcloud SDK

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

# See zone list
gcloud compute regions list

# Permanent disk
# gcloud compute disks create --size 250GB deforestprob-disk

## 1. Multiprocessing approach on one virtual machine (--num-nodes=1)
# It is better to set up a cluster as you can provide docker images for instances (not yet possible for VM, only in alpha at the moment) 
gcloud container clusters create deforestprob-cluster --machine-type=custom-24-98304 --num-nodes=1 --disk-size=250

# Set it as the default cluster
gcloud config set container/cluster deforestprob-cluster
gcloud config list

# Getting the cluster credentials
gcloud container clusters get-credentials deforestprob-cluster --zone europe-west1-d --project ee-deforestprob

# Connect to Kubernetes control panel
# kubectl proxy
# Open the Dashboard interface by navigating to the following location in the browser: http://127.0.0.1:8001/ui

# Deploy the kubernetes configuration onto the cluster
kubectl create -f gke/deforestprob.yml

# See pods and services
kubectl get deployments
kubectl get pods
kubectl get services

# Delete container
# gcloud container clusters delete deforestprob-cluster --async

## Cluster approach with several nodes
# Create cluster
# gcloud container clusters create deforestprob-cluster --machine-type=n1-standard-32 --num-nodes=1 --disk-size=250

