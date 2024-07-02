#!/bin/bash

# Ragai - (c) Eric Dodémont, 2024.

# Script which can be used to start the db server, the app, and the chroma db admin web interface.

bash db.sh start && bash app.sh start && sudo docker run -p 3000:3000 chromadb-admin &
