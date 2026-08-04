#!/usr/bin/env bash
# Build and run pyxpcsviewer in a podman container with X11 forwarding.
#
# Usage:
#   ./run_container.sh build                        # build (or rebuild) the image
#   ./run_container.sh run /path/to/hdf_folder      # run the GUI, mounted at --path
#
# "run" requires exactly one argument: a local folder containing HDF result files.
# The image is built automatically if it doesn't exist yet.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="pyxpcsviewer:latest"

do_build() {
    echo "Building $IMAGE_NAME ..."
    podman build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    echo "Done."
}

do_run() {
    if [[ $# -lt 1 ]]; then
        echo "Error: 'run' requires a path to an HDF result folder." >&2
        echo "Usage: $0 run /path/to/hdf_folder" >&2
        exit 1
    fi

    local data_dir="$1"

    # Verify the path exists and is a directory
    if [[ ! -d "$data_dir" ]]; then
        echo "Error: '$data_dir' is not a valid directory." >&2
        exit 1
    fi

    # Build the image if it doesn't exist yet
    if ! podman images --format '{{.Repository}}:{{.Tag}}' | grep -qF "$IMAGE_NAME"; then
        echo "Image not found, building $IMAGE_NAME ..."
        do_build
    fi

    podman run -it --rm \
        -e DISPLAY="$DISPLAY" \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v "$data_dir:/data:ro" \
        "$IMAGE_NAME" pyxpcsviewer --path /data
}

main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 {build|run}" >&2
        exit 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        build)
            do_build
            ;;
        run)
            do_run "$@"
            ;;
        *)
            echo "Error: unknown subcommand '$cmd'." >&2
            echo "Usage: $0 {build|run}" >&2
            exit 1
            ;;
    esac
}

main "$@"