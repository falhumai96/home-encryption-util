import os
import container_manager

if __name__ == "__main__":
    # Change the current directory to be inside the container's mount point, to
    # prevent other users from dismounting this container.
    os.chdir(container_manager._CONTAINER_MOUNT)

    # Hang the script in an infinite loop.
    while True:
        pass
