FROM ubuntu:bionic

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
    python3-pip \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*

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

# Install pip in Blender's Python
RUN ${BLENDER_PATH}/2.83/python/bin/python3.7m -m ensurepip

# Set up working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

# Install dependencies in system Python (for FastAPI)
RUN pip3 install --no-cache-dir -r requirements.txt

# Install dependencies in Blender's Python (for rendering)
RUN ${BLENDER_PATH}/2.83/python/bin/pip3 install --no-cache-dir numpy==1.21.6 pandas==1.3.4

# Copy application code
COPY . .

# Set environment variable for Blender path
ENV BLENDER_PATH=${BLENDER_PATH}/blender

# Expose the FastAPI port
EXPOSE 80

# Set the entry point to run the FastAPI server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]


