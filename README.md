# Assesment

# Kubernetes AI Assistant

## Project Overview

This project is a Flask-based AI assistant that interacts with a Kubernetes cluster to answer queries about deployed applications. It leverages the Mistral API for natural language processing to interpret user queries and retrieve relevant information from the Kubernetes API.

## Technical Requirements

- **Python Version**: 3.10
- **Flask**: Web framework for creating the API
- **Kubernetes Client**: To interact with the Kubernetes API
- **Pydantic**: For data validation
- **Requests**: For making HTTP requests to the Mistral API

## API Specifications

### Endpoint

- **URL**: `http://localhost:8000/query`
- **Method**: `POST`

### Payload Format

```json
{
    "query": "How many pods are in the default namespace?"
}
```

## Response Format
The response will be in the following format, utilizing Pydantic:

python
from pydantic import BaseModel

class QueryResponse(BaseModel):
{
    query: str
    answer: str
}
## Scope of Queries

The assistant is designed to handle read actions related to the following topics:

Pod status and counts
Node counts
Logs of resources deployed on Minikube
General Kubernetes information

## Example Queries
Q: "How many pods are in the default namespace?"
A: "There are 5 pods in the default namespace."

Q: "What is the status of the pod named 'example-pod'?"
A: "The status of the pod 'example-pod' is 'Running'."

Q: "Which pod is spawned by my-deployment?"
A: "my-deployment"

Q: "How many nodes are there in the cluster?"
A: "There are 2 nodes in the cluster."


## Setup Instructions

Prerequisites
Ensure you have Python 3.10 installed.
Have Minikube set up and running with your Kubernetes cluster.
Obtain your Mistral API key and set it as an environment variable:


### export MISTRAL_API_KEY="your_api_key_here"

Installation
Clone this repository:

bash
git clone https://github.com/yourusername/kubernetes-ai-assistant.git

cd kubernetes-ai-assistant

Create a virtual environment (optional but recommended):
bash

python -m venv venv

source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install the required packages:
bash
pip install -r requirements.txt

Running the Application
To start the Flask application, run:

bash
python Main.py
The application will be available at http://localhost:8000/query.

## Logging

The application logs all interactions and errors to agent.log. You can check this file for detailed logs and debugging information.


## Testing Your Agent

Use the following curl command to test the API:
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "How many pods are in the default namespace?"}'



## Implementation Approach

This project implements a Flask-based web application that serves as an AI assistant for querying a Kubernetes cluster. The main components of the implementation include:

1. **Flask Framework**: Used to create a RESTful API that listens for incoming queries from users.
   
2. **Kubernetes Client**: Utilizes the official Kubernetes Python client to interact with the Minikube cluster, enabling actions such as retrieving pod statuses, counting pods, and checking node counts.

3. **Mistral API Integration**: Leverages the Mistral API to process natural language queries. When a query is received, the application interprets the user's intent and dynamically determines the appropriate Kubernetes action.

4. **Structured Query Processing**: The `process_query` function analyzes the incoming query, generates a structured prompt for the Mistral API, and calls the relevant Kubernetes functions based on the LLM's interpretation.

5. **Logging**: Implemented logging to capture incoming requests, generated responses, and any errors encountered during processing, aiding in debugging and monitoring.

This approach ensures that the application can respond to a wide range of queries while maintaining clarity and structure in the codebase.



