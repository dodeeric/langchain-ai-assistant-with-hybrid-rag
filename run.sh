#!/bin/bash

# Ragai - (c) Eric Dodémont, 2024.

# Script which can be used as startup command if the app is deployed to Azure Web App service

python -m streamlit run Assistant.py --server.port 8000 --server.address 0.0.0.0