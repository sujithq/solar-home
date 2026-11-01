FROM ghcr.io/home-assistant/home-assistant:2026.10.4

COPY atomic_sample.py atomic_sensor.py patch_dsmr.py test_atomic_sample.py test_atomic_sensor.py /tmp/dsmr-patch/
RUN export PYTHONDONTWRITEBYTECODE=1 \
    && python /tmp/dsmr-patch/test_atomic_sample.py \
    && python /tmp/dsmr-patch/test_atomic_sensor.py \
    && python /tmp/dsmr-patch/patch_dsmr.py \
    && rm /tmp/dsmr-patch/atomic_sample.py /tmp/dsmr-patch/atomic_sensor.py \
        /tmp/dsmr-patch/patch_dsmr.py /tmp/dsmr-patch/test_atomic_sample.py \
        /tmp/dsmr-patch/test_atomic_sensor.py \
    && rmdir /tmp/dsmr-patch

COPY install_sungrow_dependency.py /tmp/install_sungrow_dependency.py
RUN python /tmp/install_sungrow_dependency.py \
    && rm /tmp/install_sungrow_dependency.py
