#!/bin/bash

echo "Deploying LLM SSE Server to Render..."

# Login to Render (you'll need to authenticate)
render login

# Create the service from render.yaml
render up

echo "Deployment initiated! Check your Render dashboard for status."
echo "Don't forget to set OPENAI_API_KEY in the Render dashboard environment variables!"