FROM python:3.12-slim

# Install system dependencies required for PySide6/Qt6 and other libraries
# These include OpenGL, X11, and XCB libraries needed for the GUI to display
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libegl1 \
    libdbus-1-3 \
    libfontconfig1 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the application source code
COPY . /app

# Install the application and its dependencies
RUN pip install --no-cache-dir .

# Set the default command to run the application
# When running the container, you will need to pass X11 display environment variables
# and mount the X11 socket.
CMD ["pyxpcsviewer"]