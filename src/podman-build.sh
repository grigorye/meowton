#!/bin/bash

set -e

echo "Creating/updating meowton container"

### build / create

systemctl stop meowton || true
podman rm meowton -f || true
podman build . -t meowton --pull

extra_mounts=()
for release_file in /etc/orangepi-release /etc/armbian-release; do
	if [ -f "$release_file" ]; then
		extra_mounts+=( -v "$release_file:$release_file:ro" )
	fi
done

if [ ${#extra_mounts[@]} -eq 0 ]; then
	echo "WARNING: no /etc/orangepi-release or /etc/armbian-release found on host."
	echo "         wiringOP may fail board detection inside the container."
fi

forward_env_vars=(
	MEOWTON_HARDWARE
	MEOWTON_DISABLE_CAT_READER
	MEOWTON_DISABLE_AUTO_FEED
	MEOWTON_HX711_READ_TIMEOUT_S
	MEOWTON_HX711_READ_INTERVAL_S
	MEOWTON_HX711_TIMEOUT_RECOVERY_S
)

extra_env=()
for env_name in "${forward_env_vars[@]}"; do
	if [ -n "${!env_name+x}" ]; then
		extra_env+=( -e "$env_name=${!env_name}" )
		echo "Forwarding env: $env_name=${!env_name}"
	fi
done

podman create -e MATPLOTLIB=false --stop-timeout=0 --network host --privileged --name meowton -v /etc/localtime:/etc/localtime:ro -v "$PWD":/app "${extra_mounts[@]}" "${extra_env[@]}" meowton

# add to systemctl
podman generate systemd -n meowton > /etc/systemd/system/meowton.service
systemctl daemon-reload
systemctl enable meowton --now


echo "Done: created and started meowton container."
echo "Use systemctl to start/top meowton."
echo "Use jouralctl -f to see logs."
