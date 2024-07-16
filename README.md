# WorkerNode

## Overview

`WorkerNode` is a robust system designed to facilitate API and local model node operations. It dynamically interacts with message queues and reports to management nodes for error logging and statistics.

## Environment Variables

`WorkerNode` uses environment variables to configure various settings:

- `NODE_TYPE`: Type of node (`remote` or `local`).
- `MODEL_NAME`: Name of the model in use.
- `API_URL`: URL to access the API, e.g., `https://api.openai.com`.
- `API_KEY`: Key for API access.
- `MAX_PROCESS_NUM`: Maximum number of requests that can be handled simultaneously, default is 128.
- `PULSAR_URL`: URL to connect to Pulsar.
- `PULSAR_TOKEN`: Token for connecting to Pulsar.
- `RES_TOPIC_NAME`: Topic name for sending logs/billing information.
- `DEBUG`: Debug mode, `true` enables it.
- `AIMODEL_NAME`: Current AI Model name.
- `AIMODEL_NAMESPACE`: Namespace of the current AI Model.

## Model Information

The system currently supports a single model per request. For local nodes, refer to [Mozilla-Ocho/llamafile](https://github.com/Mozilla-Ocho/llamafile) for a minimal model example. Ensure to handle model information errors appropriately.

## Error Reporting Types

High priority and critical error logs should be reported, especially irreversible errors and API quota completions. Errors such as configuration issues or authentication failures must be reported with human-readable details.

## Design Purpose and Functionality

### WorkerNodeGo

- **Purpose**: This part of the code is primarily for testing and demonstration purposes. It does not actually interface with any external APIs or local models.
- **Functionality**: The program listens to a Pulsar message queue and processes incoming messages with a simple, static response. This static response is predefined and does not involve any dynamic data processing.
- **Specifics**: It receives a task request and consistently returns the same fixed response, regardless of the specifics of the request.

### WorkerNodePython

- **Purpose**: This component is a complete working node implementation that supports real interactions with external APIs or local models.
- **Functionality**: Configured via environment variables, it can operate as either an API node or a local node, processing requests from the Pulsar message queue by invoking APIs or local models to generate responses.
- **Concurrency**: Supports multithreading, capable of handling multiple messages concurrently, and includes a more complex error handling and event logging mechanism.
- **Integration**: Includes interactions with Kubernetes clusters to facilitate operation in a containerized environment.

## Workflow

1. **Subscription to Message Queue:** Depending on the model type, subscribe to relevant topics using Shard mode. Requests are randomly assigned to a matching node.
2. **Node Types Handling:**
   - **API Node:** Handle messages based on rate limits. If the node is unavailable due to rate limits or quota completions, report to the management node.
   - **Local Node:** Start a local model process and adjust rate limits based on resource consumption.
3. **API Requests Handling:** Distinguish between `stream=true` and `stream=false` and modify request bodies as necessary to ensure unified behavior.
4. **Failure Handling:** Use `nak` for message queue if the operation fails, otherwise `ack`.
5. **Logging and Billing:** Send metadata such as timestamps, stages duration, client and model information, node and request details, and token consumption to a specific message queue.

## Rate Limits and Error Handling

Handle errors appropriately, considering different scenarios like rate limits or irreversible errors. Non-critical errors should be handled without extra reporting.

## API Specifications

- [API Specifications Document](https://github.com/uplion/main-api-service?tab=readme-ov-file#api-specification)
- Ensure compliance with message format and [error reporting](https://github.com/uplion/ai-model-operator?tab=readme-ov-file#reporting-irreversible-errors) as per guidelines.

## Error Message Specifications

Reference the OpenAI documentation for error fields: [OpenAI Error Codes](https://platform.openai.com/docs/guides/error-codes/api-errors).

## Running

Provide steps for setting up the `WorkerNode` system, including installation of dependencies, setting environment variables, and starting the service.

Before running the `WorkerNode` program, ensure the following prerequisites are met and steps are followed:

### Prerequisites

- **Python**: Ensure Python 3.6 or newer is installed on your system. You can check your Python version by running:

  ```bash
  python --version
  ```

- **Pulsar**: The program requires Apache Pulsar. You can install Pulsar or set up a Pulsar instance following the official [Pulsar documentation](https://pulsar.apache.org/docs/next/).

- **Kubernetes**: For [Kubernetes](https://kubernetes.io/docs/home/) integration, you need access to a Kubernetes cluster or a local setup using Minikube or Docker Desktop.

### Python Dependencies

Install the required Python libraries using pip. All dependencies you need is in [requirement.txt](WorkerNodePython/WorkerNode/requirement.txt)

```bash
pip install -r requirement.txt
```

### Configuration Files

Make sure to configure the necessary environment variables as outlined in the Environment Variables section of this README. These variables can be set in your shell environment or through a configuration file that you source before running the program.

### Setup Scripts

#### Running Local Scripts

If you are setting up a local model, it is necessary to run a local script named `local.sh` that is located in the current directory. This script prepares the local environment or performs necessary initializations for the local model to function correctly.

To run the script, you should first ensure that it is executable. You can set the executable permission using the following command:

```bash
chmod +x ./local.sh
```

After setting the executable permission, you can run the script directly from the terminal:

```bash
./local.sh
```

or

```bash
bash local.sh
```

#### start.sh and ai.sh

The `start.sh` script is responsible for setting up the environment by starting necessary services such as Docker containers and Apache Pulsar in your local for test. Here is how to prepare and execute this script:

**Running `start.sh` Script**

- Ensure Docker is installed and running on your system.

- Place the script in an appropriate directory and ensure it is executable:

  ```bash
  chmod +x start.sh
  ```

- Execute the script to start the services:

  ```bash
  ./start.sh
  ```

  or

  ```bash
  bash start.sh
  ```

**Script Operations:**

- **Docker Container**: Starts a Docker container with the necessary environment variables for the application.
- **Apache Pulsar**: Checks for the presence of the Apache Pulsar directory and runs it if available.
- **Error Handling**: Includes basic error handling to stop and remove the Docker container if the script fails to execute properly.

**Running ai.sh Script**

- Before running `ai.sh`, ensure that the REST API server (as started by `start.sh`) is up and running.

- Make sure the script is executable:

  ```bash
  chmod +x ai.sh
  ```

- To run the script in **non-streaming** mode:

  ```bash
  ./ai.sh
  ```

  or

  ```bash
  bash ai.sh
  ```

- To enable **streaming** mode:

  ```
  ./ai.sh stream
  ```

  or

  ```bash
  bash ai.sh stream
  ```

**Script Operations:**

- Constructs JSON data for API requests using the `jo` command, which must be installed separately (`sudo apt-get install jo` on Debian/Ubuntu or `winget install jo` in Windows).
- Sends requests to the REST API and displays verbose output using `curl`.



### Running the Program

Once all dependencies are installed and configurations are set, you can run the program using:

```bash
python3 WorkerNode.py
```

## Running with Docker

This project can be run using Docker, which simplifies setup and ensures consistency across different environments. Follow these steps to build and run the project using Docker:

### Prerequisites

- Ensure you have Docker installed on your system. You can download it from [Docker's official site](https://www.docker.com/products/docker-desktop).

### Building the Docker Image

To build the Docker image, navigate to the directory containing the Dockerfile and run the following command:

```bash
docker build -t workernode .
```

### Running the Docker Container

Once the image is built, you can run the container using:

```bash
docker run -d --network host -e PULSAR_URL=pulsar://localhost:6650 -e PORT=8081 workernode
```

### Stopping the Container

To stop the running container, you can use:

```bash
docker stop [CONTAINER_ID]
```

Replace `[CONTAINER_ID]` with the actual ID of your container. You can find the container ID by running `docker ps`.

### Additional Docker Commands

- Viewing Logs

  : To view the logs of the running container, use:

  ```bash
  docker logs [CONTAINER_ID]
  ```

- Entering the Container

  : If you need to enter the container to explore its environment or debug issues, you can use:

  ```bash
  docker exec -it [CONTAINER_ID] /bin/bash
  ```

This setup ensures that you can run the application with minimal configuration, leveraging Docker's capabilities to manage dependencies and environments.







## Usage

Illustrate typical use cases and command examples to help users understand how to interact with the `WorkerNode`.

## License

[MIT](LICENSE)
