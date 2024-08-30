#TODO: Optimize and finish off Dockerfile. Will need GStreamer support for cv2 package
# Start with a base image that includes CUDA and Python
FROM nvcr.io/nvidia/l4t-pytorch:r32.7.1-pth1.10-py3

# Set environment variables
#ENV PATH=/usr/local/cuda-10.2/bin${PATH:+:${PATH}}
#ENV LD_LIBRARY_PATH=/usr/local/cuda-10.2/lib64:$LD_LIBRARY_PATH

RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null
RUN echo 'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ bionic main' | tee /etc/apt/sources.list.d/kitware.list >/dev/null
RUN apt-get update && apt-get install -y wget

# Install system libraries
RUN apt-get update && apt-get install -y \
    liblapack-dev \
    libblas-dev \
    gfortran \
    libfreetype6-dev \
    libopenblas-base \
    libopenmpi-dev \
    libjpeg-dev \
    zlib1g-dev \
    python3-seaborn \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

#RUN python3 -m pip install opencv-python

# Install Python packages
RUN pip3 install --no-cache-dir \
    numpy==1.19.0 \
    pandas==0.22.0 \
    Pillow==8.4.0 \
    PyYAML==3.12 \
    scipy==1.5.4 \
    psutil \
    tqdm==4.64.1 \
    imutils \
    pycuda \
    opencv-python==4.3.0.38 \
    Jetson.GPIO==2.0.17 \
    jetson-stats==3.1.4

# Install torch and torchvision
#RUN wget https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl && \
#    pip3 install torch-1.10.0-cp36-cp36m-linux_aarch64.whl && \
#    rm torch-1.10.0-cp36-cp36m-linux_aarch64.whl

#RUN git clone --branch v0.11.1 https://github.com/pytorch/vision torchvision && \
#    cd torchvision && \
#    python3 setup.py install && \
#    cd .. && \
#    rm -rf torchvision

# Set the working directory
WORKDIR /app

# Copy application code
COPY . /app
