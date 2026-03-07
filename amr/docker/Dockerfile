# =============================================================================
# ROS2 Humble Docker Image fuer AMR auf Raspberry Pi 5 (Debian Trixie)
# Basis: ros:humble-ros-base (Ubuntu 22.04, arm64 multi-arch)
#
# osrf/ros:humble-desktop ist nur amd64 verfuegbar. Daher wird ros-base
# verwendet und die benoetigten Pakete einzeln installiert.
# =============================================================================

FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

# ---------------------------------------------------------------------------
# 1. ROS2-Pakete aus Abschnitt 2.1 + GUI-Komponenten fuer RViz2
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # RViz2 und GUI (ersetzt humble-desktop)
    ros-humble-rviz2 \
    ros-humble-rqt \
    ros-humble-rqt-common-plugins \
    # Navigation & SLAM
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    ros-humble-rplidar-ros \
    # Vision
    ros-humble-cv-bridge \
    ros-humble-v4l2-camera \
    # Build-Tools
    python3-colcon-common-extensions \
    python3-rosdep \
    # Python-Bibliotheken
    python3-numpy \
    python3-matplotlib \
    python3-opencv \
    # System-Tools
    usbutils \
    alsa-utils \
    nano \
    iputils-ping \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# 2. micro-ROS Agent: apt-Versuch, Fallback auf Source-Build
#    micro-ros-agent und micro-ros-msgs fehlen oft fuer arm64, daher
#    werden beide Repos geclont und gemeinsam gebaut.
# ---------------------------------------------------------------------------
RUN apt-get update && \
    (apt-get install -y --no-install-recommends ros-humble-micro-ros-agent \
     && rm -rf /var/lib/apt/lists/* \
    ) || ( \
        echo ">>> apt-Paket nicht verfuegbar, baue micro-ROS Agent aus Source..." && \
        rm -rf /var/lib/apt/lists/* && \
        apt-get update && \
        apt-get install -y --no-install-recommends \
            build-essential \
            cmake \
            python3-pip \
        && rm -rf /var/lib/apt/lists/* && \
        mkdir -p /opt/microros_ws/src && \
        cd /opt/microros_ws && \
        . /opt/ros/humble/setup.sh && \
        git clone -b humble https://github.com/micro-ROS/micro-ROS-Agent.git src/micro-ROS-Agent && \
        git clone -b humble https://github.com/micro-ROS/micro_ros_msgs.git src/micro_ros_msgs && \
        rosdep install --from-paths src --ignore-src -y --skip-keys=micro_ros_msgs && \
        colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release && \
        rm -rf build log src/*/.git \
    )

# ---------------------------------------------------------------------------
# 3. rosdep initialisieren (falls nicht bereits geschehen)
# ---------------------------------------------------------------------------
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then \
        rosdep init; \
    fi && \
    rosdep update --rosdistro=$ROS_DISTRO

# ---------------------------------------------------------------------------
# 4. Workspace-Verzeichnis vorbereiten
# ---------------------------------------------------------------------------
RUN mkdir -p /ros2_ws/src

# ---------------------------------------------------------------------------
# 5. Shell-Konfiguration
# ---------------------------------------------------------------------------
RUN echo "# ROS2 Humble" >> /root/.bashrc && \
    echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "" >> /root/.bashrc && \
    echo "# micro-ROS Agent Workspace (falls Source-Build)" >> /root/.bashrc && \
    echo "if [ -f /opt/microros_ws/install/setup.bash ]; then" >> /root/.bashrc && \
    echo "    source /opt/microros_ws/install/setup.bash" >> /root/.bashrc && \
    echo "fi" >> /root/.bashrc && \
    echo "" >> /root/.bashrc && \
    echo "# Projekt-Workspace" >> /root/.bashrc && \
    echo "if [ -f /ros2_ws/install/setup.bash ]; then" >> /root/.bashrc && \
    echo "    source /ros2_ws/install/setup.bash" >> /root/.bashrc && \
    echo "fi" >> /root/.bashrc && \
    echo "" >> /root/.bashrc && \
    echo "cd /ros2_ws" >> /root/.bashrc

# ---------------------------------------------------------------------------
# 5b. Python-Abhaengigkeiten (WebSocket, Vision-Pipeline)
#     hailort ist NICHT via PyPI verfuegbar — wird auf dem Host ueber das
#     Raspberry Pi OS apt-Paket (python3-hailort) installiert. Die native
#     .so (cpython-313) ist inkompatibel mit dem Container (cpython-310).
#     hailo_inference_node prueft zur Laufzeit via HAS_HAILO-Flag.
# ---------------------------------------------------------------------------
RUN pip3 install --no-cache-dir \
    websockets \
    google-genai \
    python-can

WORKDIR /ros2_ws

COPY amr/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
