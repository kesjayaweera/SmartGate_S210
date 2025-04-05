# Building and Running the SmartGate Web App

This guide walks you through building the Docker images required to run the SmartGate web app using Docker Compose.

## Prerequisites

- Docker installed on your machine. Follow the [Official Docker Installation Guide](https://docs.docker.com/get-docker/) if you haven't already.
-  Docker Compose installed (usually included with Docker Desktop or available separately). Follow the [Docker Compose Install Guide](https://docs.docker.com/compose/install/) if you can't access docker-compose.
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
Now, Build the images using the docker-compose file in the current directory.

```bash
docker-compose up --build -d
```

This will build and start the containers in detached mode, meaning they will run in the background.

Alternatively, you can run the docker images without detached mode by doing:

```bash
docker-compose up --build 
```

### 4. Run the image as a docker container
After the image is built and running in detached mode. You can enter the container's bash shell by doing:

```bash
docker-compose exec sgwebimage bash 
```

Alternatively, If the image is built and **not running** in detached mode. You can enter the containers bash in a different terminal.

```bash
docker exec -it sgwebimage bash
```

This ensures you can interact with the container as needed.  

**Note:** When opening another terminal, make sure you're in `cd src/web-app`.

## SmartGate Web App Commands

Run Python Web App
```bash
python app.py
```

Access SmartGate Database Inside Docker Container
```bash
psql -h postgres -U admin -d smartgatedb
```

Access SmartGate Database Outside Docker Container
```bash
psql -h localhost -U admin -d smartgatedb
```

Database Password: smartgate (see `docker-compose.yml`)

This will start the containers allowing you to run Docker commands and access necessary services.

This `README.md` will guide users through the steps needed to clone the repository, build the images in docker compose file, and run it locally, enabling the container to communicate with the containers on the host machine.

## Important Notes for Developers

- If you make changes to the `requirements.txt`, `Dockerfile`, or `docker-compose.yml`, make sure to rebuild the images using __Step 3__

- If you make **changes to the sql files** or **stop the docker-compose from running** be sure to remove the docker volumes and containers related to the web-app by doing:

  Linux and MacOS:
  ```bash
  ./cleanup.sh
  ```

  Windows:
  ```powershell
  .\cleanup.ps1
  ```

This will give you a fresh build of the images to be run as containers after you do __Step 3__

  
