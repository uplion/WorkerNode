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

The system currently supports a single model per request. For local nodes, refer to [this GitHub repository](https://github.com/Mozilla-Ocho/llamafile) for a minimal model example. Ensure to handle model information errors appropriately.

## Error Reporting Types

High priority and critical error logs should be reported, especially irreversible errors and API quota completions. Errors such as configuration issues or authentication failures must be reported with human-readable details.

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

- [API Specifications Document](https://www.notion.so/API-5827e55421184ea58716ca67cd04da1b?pvs=21)
- Ensure compliance with message format and error reporting as per guidelines.

## Error Message Specifications

Reference the OpenAI documentation for error fields: [OpenAI Error Codes](https://platform.openai.com/docs/guides/error-codes/api-errors).

## Installation

Provide steps for setting up the `WorkerNode` system, including installation of dependencies, setting environment variables, and starting the service.

Before running the `WorkerNode` program, ensure the following prerequisites are met and steps are followed:

### Prerequisites

- **Python**: Ensure Python 3.6 or newer is installed on your system. You can check your Python version by running:

  ```bash
  python --version
  ```

- **Pulsar**: The program requires Apache Pulsar. You can install Pulsar or set up a Pulsar instance following the official Pulsar documentation.

- **Kubernetes**: For Kubernetes integration, you need access to a Kubernetes cluster or a local setup using Minikube or Docker Desktop.

### Python Dependencies

Install the required Python libraries using pip. Here's a list of essential libraries:

- **pulsar-client**: For interacting with Apache Pulsar.
- **requests**: For making HTTP requests.
- **kubernetes**: For Kubernetes API interactions.
  You can install these libraries using the following command:

```bash
pip install pulsar-client requests kubernetes
```

### Configuration Files

Make sure to configure the necessary environment variables as outlined in the Environment Variables section of this README. These variables can be set in your shell environment or through a configuration file that you source before running the program.

### Setup Scripts

#### Running Local Scripts

If you are setting up a local model, it is necessary to run a local script named `bash.sh` that is located in the current directory. This script prepares the local environment or performs necessary initializations for the local model to function correctly.

To run the script, you should first ensure that it is executable. You can set the executable permission using the following command:

```bash
chmod +x ./local.sh
```

After setting the executable permission, you can run the script directly from the terminal:

```bash
./local.sh
```

#### start.sh and ai.sh

The `start.sh` script is responsible for setting up the environment by starting necessary services such as Docker containers and Apache Pulsar. Here is how to prepare and execute this script:

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

- To run the script in non-streaming mode:

  ```bash
  ./ai.sh
  ```

- To enable streaming mode:

  ```
  ./ai.sh stream
  ```

**Script Operations:**

- Constructs JSON data for API requests using the `jo` command, which must be installed separately (`sudo apt-get install jo` on Debian/Ubuntu).
- Sends requests to the REST API and displays verbose output using `curl`.



### Running the Program

Once all dependencies are installed and configurations are set, you can run the program using:

```bash
python3 WorkerNode.py
```



## Usage

Illustrate typical use cases and command examples to help users understand how to interact with the `WorkerNode`.

## License

MIT https://github.com/uplion/WorkerNode?tab=MIT-1-ov-file#
