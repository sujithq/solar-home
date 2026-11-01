FROM ghcr.io/home-assistant/home-assistant:2026.10.4

COPY install_sungrow_dependency.py /tmp/install_sungrow_dependency.py
RUN python /tmp/install_sungrow_dependency.py \
    && rm /tmp/install_sungrow_dependency.py
