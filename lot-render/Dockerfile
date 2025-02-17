FROM ubuntu:focal

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libfreetype6 \
    libglu1-mesa \
    libxi6 \
    libxrender1 \
    xz-utils \
    unzip \
    p7zip-full \
    software-properties-common \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3.9-distutils \
    build-essential \
    libpq-dev \
    gcc \
    libc-dev \
    libffi-dev \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.9
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9

# Set Blender variables
ENV BLENDER_VERSION="2.83.0"
ENV BLENDER_PACKAGE_NAME="blender-${BLENDER_VERSION}-linux64"
ENV BLENDER_PACKAGE_URL="https://download.blender.org/release/Blender2.83/${BLENDER_PACKAGE_NAME}.tar.xz"
ENV BLENDER_PATH="/usr/local/blender"
ENV BLENDER_PYTHON_PATH="${BLENDER_PATH}/2.83/python/bin"
ENV PYTHONPATH="/app"

# Download and install Blender
WORKDIR /tmp
RUN curl -OL ${BLENDER_PACKAGE_URL} \
    && tar -xJf ${BLENDER_PACKAGE_NAME}.tar.xz -C /tmp \
    && rm -f ${BLENDER_PACKAGE_NAME}.tar.xz \
    && mv /tmp/${BLENDER_PACKAGE_NAME} ${BLENDER_PATH}

# Create addons directory
RUN mkdir -p ${BLENDER_PATH}/2.83/scripts/addons

# Install pip in Blender's Python and upgrade it
RUN ${BLENDER_PATH}/2.83/python/bin/python3.7m -m ensurepip && \
    ${BLENDER_PATH}/2.83/python/bin/pip3 install --upgrade pip

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

# Install dependencies in system Python (for FastAPI)
RUN python3.9 -m pip install --no-cache-dir -r requirements.txt

# Install dependencies in Blender's Python (for rendering)
RUN ${BLENDER_PATH}/2.83/python/bin/pip3 install --no-cache-dir \
    numpy==1.19.5 \
    pandas==1.1.5 \
    scipy==1.7.3 \
    Pillow==8.4.0

# Create models directory and download YOLO model
# RUN mkdir -p /app/models && \
#     curl -L "https://storage.cloud.google.com/gethome-files/computational-vision/models/zoom_20/yolo-best-models/zoom_20/best.pt?authuser=2" -o /app/models/best.pt

# Copy application code
COPY . .

# Set environment variable for Blender path
ENV BLENDER_PATH=${BLENDER_PATH}/blender

# Expose the FastAPI port
EXPOSE 80

# Set the entry point to run the FastAPI server
CMD ["python3.9", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]


