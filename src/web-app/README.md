# Building and Running the SmartGate Web App

This guide walks you through building the Docker images required to run the SmartGate web app.

## Prerequisites

- Docker installed on your machine. Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) if you haven't already.
-  Docker Compose installed (usually included with Docker Desktop or available separately). Follow the [Docker Compose Install Guide](https://docs.docker.com/compose/install/) if you can't access docker-compose.
- If you are using macOS or Windows, please install Docker Desktop. Follow the [Docker Desktop for Mac and Windows](https://www.docker.com/products/docker-desktop)
- Access to a terminal (Linux/macOS) or a terminal emulator like Git Bash (Windows).
-  Git installed. You can download it from [Git Install Guides](https://github.com/git-guides/install-git)
-  Internet Access is required to download the [Python](https://hub.docker.com/layers/library/python/3.9.21-bookworm/images/sha256-5097c91412f578fe1ac80236fb00e70170aa368daae8f02daebffd3541022abb) and [Postgres](https://hub.docker.com/layers/library/postgres/13/images/sha256-dce7bae4d506b2de20fd95f62a449ae1fd24b5d82f75e58246237becd9ff1c5d) images from Docker Hub.

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
### 3. Build the docker images
Now, Build the images using docker-compose using the file in the current directory.

```bash
docker-compose up --build
```
### 4. Run the image as a docker container
After the image is built make a new terminal and enter the container's bash shell by doing:

```bash
docker-compose exec sgwebimage bash
```
## Commands To Run For SmartGate Web App In Container's Shell

Run Python Web App
```bash
python app.py
```

Access SmartGate Database
```bash
psql -h postgres -p 5432 -U admin -d smartgatedb
```
Password: smartgate

This will start the containers allowing you to run Docker commands and access necessary services.

This `README.md` will guide users through the steps needed to clone the repository, build the images Docker Compose file, and run it locally, enabling the container to communicate with the containers on the host machine.

