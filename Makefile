#This is to build the Docker image, more info and alternative scripts will be provided

#Run shell environment of Docker image
run:
	sudo docker run --privileged --runtime nvidia --device /dev/gpiochip0 -it smartgate:latest /bin/bash

#Build docker environment
build:
	sudo docker build -t smartgate:latest .
