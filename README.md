# SmartGate

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
https://img.shields.io/badge/License-GPLv3-blue.svg

## Table of Contents

- [Features](#features) 
- [Requirements](#requirements) 
- [Setup](#setup) 
- [Usage](#usage) 

Utilizing real-time object detection for endangered animal species under the Jetson Nano using TensorRT engine optimization. This detection model will be used to determine the state of the hardware-configured gate.

## Features

Features include:

- Real-time object detection to set the state of the physical gate. The rules are set within the `config/` folder to set the list of stimuli that triggers the specified state of the gate (more details in [Setup](#setup)).

- Utilizing TensorRT engine optimization to enhance inference performance under the Jetson Nano. The optimized models are saved as `.engine` files within the `models/` folder. Models are obtained from the [Marsupial](https://github.com/carlosclaiton/marsupial) dataset.

- Web server dashboard to view a live feed fetched from the camera as well as manually control state of the door.

## Requirements

`Work in progress`

## Setup

`Work in progress`

## Usage

To get started run the following

```
git clone https://github.com/TheOpenSI/SmartGate.git
cd SmartGate/src/main/
python3 live_detection.py
```

