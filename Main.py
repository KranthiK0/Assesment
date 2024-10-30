import logging
from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from kubernetes import client, config
import os
import requests
import re

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    filename='agent.log', filemode='a')

# Load Kubernetes configuration (Minikube configuration)
config.load_kube_config()

# Mistral API setup
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Define Pydantic response model
class QueryResponse(BaseModel):
    query: str
    answer: str

# Function to interact with Mistral API for generating responses
def generate_mistral_response(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7
    }
    response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

def get_pod_status(pod_name, namespace="default"):
    v1 = client.CoreV1Api()
    try:
        # Log the pod name and namespace for debugging
        logging.info(f"Attempting to get status for pod '{pod_name}' in namespace '{namespace}'")
        
        # Attempt to retrieve the pod status
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        return pod.status.phase
    except client.exceptions.ApiException as e:
        # Handle specific case where pod is not found
        if e.status == 404:
            logging.error(f"Pod '{pod_name}' not found in namespace '{namespace}'.")
            return "Pod not found."
        else:
            logging.error(f"API exception when retrieving status for pod '{pod_name}': {e}")
            return "An error occurred while retrieving pod status."
    except Exception as e:
        logging.error(f"Unexpected error when retrieving status for pod '{pod_name}': {e}")
        return "An unexpected error occurred while retrieving pod status."

def get_pods_by_deployment(deployment_name, namespace="default"):
    v1 = client.CoreV1Api()
    try:
        # List pods with a label selector based on deployment name
        pods = v1.list_namespaced_pod(namespace, label_selector=f"app={deployment_name}")
        if pods.items:
            return deployment_name  # Return only the deployment name if pods are found
        else:
            return f"No pods found for deployment '{deployment_name}'."
    except client.exceptions.ApiException as e:
        logging.error(f"API exception when retrieving pods for deployment '{deployment_name}': {e}")
        return "An error occurred while retrieving pods for the deployment."
    except Exception as e:
        logging.error(f"Unexpected error when retrieving pods for deployment '{deployment_name}': {e}")
        return "An unexpected error occurred while retrieving pods for the deployment."

def process_query(query):
    try:
        # Updated structured prompt to include deployment example
        structured_prompt = f"""
        You are a Kubernetes assistant. Given a user query, identify the Kubernetes action needed. Here are some examples:
        
        - "How many pods are in the default namespace?" -> count pods
        - "List all pods in the default namespace." -> list all pods
        - "What is the status of the pod named 'example-pod'?" -> check pod status
        - "How many nodes are there in the cluster?" -> count nodes
        - "Is the API server accessible?" -> check API server
        - "Which pod is spawned by my-deployment?" -> list pods for deployment

        Based on this, interpret the following query: "{query}"
        """
        intent_response = generate_mistral_response(structured_prompt)
        
        # Determine action based on LLM interpretation
        if "count pods" in intent_response:
            pod_count = len(get_pods())
            return f"There are {pod_count} pods in the default namespace."
        elif "list all pods" in intent_response:
            pod_names = get_pods()
            return ", ".join(pod_names)
        elif "check pod status" in intent_response:
            pod_name = re.findall(r"named\s+'?([\w\-\d]+)'?", query)
            pod_name = pod_name[0] if pod_name else None
            if pod_name:
                pod_status = get_pod_status(pod_name)
                return f"The status of the pod '{pod_name}' is '{pod_status}'."
            else:
                return "Invalid pod name format in query."
        elif "count nodes" in intent_response:
            node_count = get_node_count()
            return f"There are {node_count} nodes in the cluster."
        elif "check API server" in intent_response:
            return is_api_server_accessible()
        elif "list pods for deployment" in intent_response:
            deployment_name = re.findall(r"by\s+([\w\-\d]+)", query)
            deployment_name = deployment_name[0] if deployment_name else None
            if deployment_name:
                pod_names = get_pods_by_deployment(deployment_name)
                return f"The pod(s) spawned by deployment '{deployment_name}' are: {pod_names}"
            else:
                return "Invalid deployment name format in query."
        else:
            return "I'm sorry, I couldn't determine the action for this query."

    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        return f"An error occurred while processing your query: {str(e)}"


# Core Kubernetes interaction functions
def get_pods(namespace="default"):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace)
    return [pod.metadata.name for pod in pods.items]


def get_node_count():
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    return len(nodes.items)

def is_api_server_accessible():
    v1 = client.CoreV1Api()
    try:
        # Attempt to access the API server to check availability
        v1.get_api_resources()
        return "Yes"
    except Exception as e:
        # Log the error if access fails
        logging.error(f"Error accessing the API server: {e}")
        return "No"


# Main function to process queries dynamically using LLM

# Flask route for querying
@app.route('/query', methods=['POST'])
def create_query():
    try:
        # Parse the incoming JSON request data
        request_data = request.get_json()
        query = request_data.get('query')

        # Log the received query
        logging.info(f"Received query: {query}")

        # Process the query
        answer = process_query(query)

        # Log the generated answer
        logging.info(f"Generated answer: {answer}")

        # Create the response using Pydantic model
        response = QueryResponse(query=query, answer=answer)
        return jsonify(response.dict())
    
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return jsonify({"error": e.errors()}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
