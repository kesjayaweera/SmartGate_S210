# SmartGate

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![python](https://img.shields.io/badge/Python-3.6-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

## Table of Contents

- [Features](#features) 
- [Requirements](#requirements) 
- [Setup](#setup) 
- [Usage](#usage)
- [Contributing](#contributing)

Utilizing real-time object detection for endangered animal species under the Jetson Nano using TensorRT engine optimization. This detection model will be used to determine the state of the hardware-configured gate.

## Features

Features include:

- Real-time object detection to set the state of the physical gate. The rules are set within the `config/` folder. The `config.json` file contains the general rules to set the list of stimuli that triggers the specified state of the gate (more details in [Setup](#setup)).

- Utilizing TensorRT engine optimization to enhance inference performance under the Jetson Nano. The optimized models are saved as `.engine` files within the `models/` folder. Models are obtained from the [Marsupial](https://github.com/carlosclaiton/marsupial) dataset.

- Web server dashboard to view a live feed fetched from the camera as well as manually control state of the door.

## Requirements

Installing the requirements should be ran under the Jetson Nano with the Jetpack SDK. For more info on setting this up, please refer to NVIDIA's official guides for your respective Jetson Nano model: 

- [Jetson Nano 4GB](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit) 
- [Jetson Nano 2GB](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-2gb-devkit).

There are two options users can use to set up the requirements.

1. Install the dependencies locally on the Nano.

```sh
git clone https://github.com/TheOpenSI/SmartGate.git
cd SmartGate/setup
./setup_requirements.sh
```

Optional: Generate the systemd service and automatically enable and start the service to run on boot. 
```sh
cd SmartGate/setup
./systemd_service_setup.sh
```

2. Build Docker container.

```sh
git clone https://github.com/TheOpenSI/SmartGate.git
cd SmartGate/
sudo docker build -t smartgate:latest .
```

## Setup

**Ensure the [Requirements](#requirements) are satisfied before proceeding.**

Users are free to configure the rules to set the behaviour of the gate specified on a list of stimuli. Within `config/config.json` a base template would be provided with:

```json
{
     "model": {
        "path": "../models/yolov5s.engine",
        "classes": "../models/classes/yolov5s.txt",
        "confidence": 0.5
    },

    "rules": [
        {
            "objects": ["dog"],
            "action": "OPEN"
        },
        {
            "objects": ["cat"],
            "action": "CLOSE"
        }
    ],
    
    "server": {
        "port": 8080
    }
}
```

### Model Configuration

*Note that in the configuration file, any path specified can be relative to the location of the configuration file itself.*

- The `model` section defines the settings for the object detection model
    - `path` specifies the file path to the trained model (in this case, a YOLOv5 model in TensorRT format). If you are working with a `.pt` file, you will need to convert it to a `.engine` file. You can use the following [repo](https://github.com/mailrocketsystems/JetsonYolov5) to convert it, or follow this [tutorial](https://youtube.com/watch?v=ErWC3nBuV6k)
    - `classes` points to a text file containing the list of object classes the model can detect. It will need to be in the following format `index: class` (check the files in `models/classes` for some examples)
    - `confidence` sets the confidence threshold for object detection (`0.5` or 50% in this example).

### Rules Configuration

- `rules` section define how the gate should respond to detected objects
    - `objects` array represents the list of strings of the objects that should trigger the specified `action`. This should be referred from your specified classes file (from `models/classes`)
    - `action` is the action to take when the specified objects from `objects` are detected. Can be either `OPEN` or `CLOSE`.

- In this example:

    - If `dog` is detected the gate should open
    - If `cat` is detected the gate should close
    - If both are detected the gate should close. This should be the default behaviour of the SmartGate when both stimuli are detected

### Server Configuration

- `server` section contains the settings for the web server
    - `port` is the port number for which the web server would run under. In the example it's set to `8080` 

## Usage

**Ensure the [Requirements](#requirements) are satisfied before proceeding.**

To get started run the following 

```sh
cd SmartGate/src/main/
python3 live_detection.py
```

A web server should run in which the camera stream can be viewed from the main dashboard.

## Contributing

`Work in Progress`
