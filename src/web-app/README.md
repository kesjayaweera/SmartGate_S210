# Building and Running the SmartGate Docker Image

This guide will walk you through the process of building the SmartGate Docker image and running it as a container in privileged mode.

## Prerequisites

- Docker installed on your machine. Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) if you haven't already.
- If you are using macOS or Windows, please install Docker Desktop. Follow the [Docker Desktop for Mac and Windows](https://www.docker.com/products/docker-desktop)
- Access to a terminal (Linux/macOS) or a terminal emulator like Git Bash (Windows).
- A GitHub repository to clone (in this case, the SmartGate repository).

## Steps

### 1. Clone the Repository

First, clone the SmartGate repository to your local machine.

```bash
git clone https://github.com/ChristopherLaff/SmartGate.git
cd SmartGate
```
### 2. Navigate to `src/web-app` directory
Once you're in the `SmartGate` directory, navigate to the `src/web-app` directory.

```bash
cd src/web-app
```
### 3. Build the docker image 
Now, build the Docker image using the `Dockerfile` in the current directory.

```bash
docker build -t smartgate-image .
```
### 4. Run the image as a docker container
After the image is built, run it as a container in privileged mode using the following command:

Linux:
```bash
docker run -it --privileged --name smartgate-container -v /var/run/docker.sock:/var/run/docker.sock smartgate-image
```

Windows:
```bash
docker run -it --privileged --name smartgate-container smartgate-image
```

MacOS:
```bash
docker run -it --name smartgate-container -v /var/run/docker.sock:/var/run/docker.sock -p 8000:8000 -p 5432:5432 smartgate-image
```

This will start the container with Docker capabilities inside the container, allowing you to run Docker commands and access necessary services.

This `README.md` will guide users through the steps needed to clone the repository, build the Docker image, and run it in privileged mode with the Docker socket mounted, enabling the container to communicate with the Docker daemon on the host machine.

