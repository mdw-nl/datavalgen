# Note/TODO: IMHO a program should be as environment-agnostic as possible, it
# shoudn't need to be aware that it's running in a docker container. But to
# provide users with a single command (`docker run`) they can run to validate
# their data, we need to have some docker-specific code.
from pathlib import Path
import sys
import os


# if "/data/.dockerfile" contains the canary string which was created on
# container-fs during build, we warn user they might've forgotten volume-map
# host dir with data onto /data
def docker_detect_missing_volume(out_path) -> bool:
    """
    Returns True if:
      * running in docker
      * missing volume map /data is detected.
      * tyring to write to /data
    """
    internal_data_marker = Path("/data/.dockerfile")

    if (
        _running_on_docker()
        and out_path.resolve().parent == Path("/data")
        and internal_data_marker.is_file()
        and internal_data_marker.read_text().strip()
        == "file-on-directory-created-during-docker-build"
    ):
        print(
            "⚠️  It looks like you tried to write to the /data directory and you are running this tool via docker\n"
            "    However, it doesn't look like you mounted a volume on /data.\n"
            "    You probably meant to run this command with something like:\n"
            "    docker run -v ./data:/data ...\n",
            "    Aborting...",
            file=sys.stderr,
        )
        return True

    return False


# Problem: writing to /data/data.csv from within the container will mean
# root:root file. If `docker run` was run by a user, we will annoy them.
# So we fix the output file permissions to match /data dir.
def docker_fix_permissions(out_path: Path) -> None:
    """
    If running in docker and writing to /data, fix permissions of the output file
    to match the data directory.

    Return True if it had to change permissions, False otherwise.
    """
    if not _running_on_docker() or not out_path.resolve().parent == Path("/data"):
        return False

    data_dir = out_path.resolve().parent
    owner = data_dir.stat().st_uid
    group = data_dir.stat().st_gid
    print(
        f"Changing ownership of output file to match data directory: {data_dir} ({owner}:{group})"
    )
    os.chown(out_path, owner, group)

    return True


# Looks for env var DATAVALGEN_DOCKER, typically set in Dockerfile
def _running_on_docker() -> bool:
    """
    Returns True if running in docker container (based on env var).
    """
    return os.getenv("DATAVALGEN_DOCKER", "false").lower() == "true"
