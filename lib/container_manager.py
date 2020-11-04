import subprocess
import os
import sys
import util
import psutil
import shutil
import time


_CONTAINER_LOCATION = "/root/.encrypted_home_container.hc"
_CONTAINER_MOUNT = "/root/.encrypted_home_container"
_HOME_ENCRYPTION_UTIL_TMP_LOCATION = "/root/.home_encryption_util_tmp"
_ORIGINAL_SWAP_TMP = os.path.join(
    _HOME_ENCRYPTION_UTIL_TMP_LOCATION, "original_swap")
_ENCRYPTED_HOME_FOLDERS = os.path.join(_CONTAINER_MOUNT, "home")
_ENCRYPTED_SWAP_LOCATION = os.path.join(_CONTAINER_MOUNT, "enc_swap.img")


def _get_proc_visibility():
    current_proc_options = subprocess.check_output([
        "findmnt", "-n", "-o", "options", "/proc"
    ]).decode("UTF-8").strip().split(",")
    try:
        option_level_text = [
            option for option in current_proc_options if option.startswith("hidepid=")][0]
        option_level_value = option_level_text.split("=")[1]
        if option_level_value == "invisible":
            return str(2)
        else:
            return str(1)
    except IndexError:
        return str(0)


def _hide_proc():
    try:
        current_proc_visibility = _get_proc_visibility()
        ret = util.silent_execute([
            "mount", "-o", "remount,hidepid=2", "/proc"
        ])
        if ret:
            return None
        return current_proc_visibility
    except subprocess.CalledProcessError as e:
        print(str(e))
        return None


def _restore_proc_visibility(original_proc_visibility):
    return util.silent_execute([
        "mount", "-o", "remount,hidepid={proc_visibility}".format(
            proc_visibility=str(original_proc_visibility)), "/proc"
    ]) == 0


def _is_container_mounted():
    global _CONTAINER_LOCATION
    global _CONTAINER_MOUNT

    return util.silent_execute([
        "veracrypt", "--text", "--list", _CONTAINER_LOCATION
    ]) == 0 and util.is_dir_mounted(_CONTAINER_MOUNT)


def lock_container():
    global _CONTAINER_MOUNT
    global _ENCRYPTED_HOME_FOLDERS
    global _ENCRYPTED_SWAP_LOCATION
    global _CONTAINER_LOCATION
    global _ORIGINAL_SWAP_TMP

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Check if the container is not mounted.
    if not _is_container_mounted():
        print("Container is not mounted!")
        return 0

    # Dismount all encrypted users' home folders, killing all their running processes.
    if os.path.exists(_ENCRYPTED_HOME_FOLDERS):
        for user in os.listdir(_ENCRYPTED_HOME_FOLDERS):
            if util.is_dir_mounted("/home/" + user):
                util.kill_all_processes_owning_a_folder("/home/" + user)
                ret = util.silent_execute([
                    "umount", "/home/" + user
                ])
                if ret:
                    util.eprint(
                        "Could not unmount {user}'s encrypted home folder!".format(user=user))
                if util.is_dir_mounted("/home/" + user):
                    ret = util.silent_execute([
                        "umount", "-l", "/home/" + user
                    ])
                    if ret:
                        util.eprint(
                            "Could not lazy unmount {user}'s encrypted home folder!".format(user=user))
                        return ret

    util.kill_all_processes_owning_a_folder(_CONTAINER_MOUNT)

    # Swap off the encrypted swap image, and restore the original swap images.
    if os.path.exists(_ENCRYPTED_SWAP_LOCATION):
        util.silent_execute([
            "swapon", _ENCRYPTED_SWAP_LOCATION
        ])
        ret = util.silent_execute([
            "swapoff", _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint("Could not swap off the encrypted swap file!")
            return ret
    if os.path.exists(_ORIGINAL_SWAP_TMP):
        with open(_ORIGINAL_SWAP_TMP, "r") as fd:
            original_swap_text = fd.read().strip()
            original_swaps = original_swap_text.split(os.linesep)
            for swap in original_swaps:
                if swap.strip():
                    util.silent_execute([
                        "swapoff", swap.strip()
                    ])
                    ret = util.silent_execute([
                        "swapon", swap.strip()
                    ])
                    if ret:
                        util.eprint("Could not swap on {swap}!".format(
                            swap=swap.strip()))
                        return ret

    # Lock the container.
    ret = util.silent_execute([
        "veracrypt", "--text", "--dismount", _CONTAINER_LOCATION
    ])
    if ret:
        util.eprint("Could not lock the container!")
        return ret

    return 0


def unlock_container(password):
    global _CONTAINER_LOCATION
    global _CONTAINER_MOUNT
    global _ENCRYPTED_HOME_FOLDERS
    global _ENCRYPTED_SWAP_LOCATION
    global _HOME_ENCRYPTION_UTIL_TMP_LOCATION
    global _ORIGINAL_SWAP_TMP

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Check if the container is mounted.
    if _is_container_mounted():
        print("Container is mounted already!")
        return 0

    # Make sure the container is truly dismounted from VeraCrypt.
    util.silent_execute([
        "veracrypt", "--text", "--dismount", _CONTAINER_LOCATION
    ])

    # Unlock the container.
    original_proc_visibility = _hide_proc()
    while not original_proc_visibility:
        util.eprint("Could not hide root processes! Trying again...")
        time.sleep(2)
        original_proc_visibility = _hide_proc()
    try:
        os.makedirs(_CONTAINER_MOUNT, exist_ok=True)
    except OSError:
        util.eprint("Could not create the countainer's mount point folder!")
        while not _restore_proc_visibility(original_proc_visibility):
            util.eprint(
                "Could not restore root processes visibility! Trying again...")
            time.sleep(2)
        return 1
    ret = util.silent_execute([
        "veracrypt", "--text", "--password", password, "--non-interactive",
        _CONTAINER_LOCATION, _CONTAINER_MOUNT
    ])
    if ret:
        util.eprint("Could not unlock the container!")
        while not _restore_proc_visibility(original_proc_visibility):
            util.eprint(
                "Could not restore root processes visibility! Trying again...")
            time.sleep(2)
        return ret
    while not _restore_proc_visibility(original_proc_visibility):
        util.eprint(
            "Could not restore root processes visibility! Trying again...")
        time.sleep(2)

    # Record and swap off the current swap images/partitions,
    # and use the encrypted swap instead.
    try:
        os.makedirs(_HOME_ENCRYPTION_UTIL_TMP_LOCATION, exist_ok=True)
    except OSError:
        util.eprint("Could not create the utility's temporary folder!")
        return 1
    with open(_ORIGINAL_SWAP_TMP, "w") as fd:
        original_swap_text = None
        try:
            original_swap_text = subprocess.check_output([
                "swapon", "--show=name", "--noheadings"
            ]).decode("UTF-8").strip()
        except subprocess.CalledProcessError:
            util.eprint("Could not get the original swap locations!")
            return 1
        original_swaps = original_swap_text.split(os.linesep)
        fd.write(original_swap_text)
        for swap in original_swaps:
            if swap.strip():
                util.silent_execute([
                    "swapon", swap.strip()
                ])
                ret = util.silent_execute([
                    "swapoff", swap.strip()
                ])
                if ret:
                    util.eprint("Could not swap off {swap}!".format(
                        swap=swap.strip()))
                    return ret
    if os.path.exists(_ENCRYPTED_SWAP_LOCATION):
        util.silent_execute([
            "swapoff", _ENCRYPTED_SWAP_LOCATION
        ])
        ret = util.silent_execute([
            "swapon", _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint("Could not swap on the encrypted swap file!")
            return ret

    # Run the looper Python process as root on the container directory to disallow
    # non-root users from dismounting the container.
    subprocess.Popen([
        sys.executable, os.path.join(os.path.dirname(__file__), "looper.py")
    ], start_new_session=True)

    # Mount all encrypted users.
    if os.path.exists(_ENCRYPTED_HOME_FOLDERS):
        for user in os.listdir(_ENCRYPTED_HOME_FOLDERS):
            try:
                os.makedirs("/home/" + user, exist_ok=True)
            except OSError:
                util.eprint(
                    "Could not create {user}'s home folder's encryption mount point!".format(user=user))
                return 1
            ret = util.silent_execute([
                "mount", "--bind", os.path.join(_ENCRYPTED_HOME_FOLDERS,
                                                user), "/home/" + user
            ])
            if ret:
                util.eprint(
                    "Could not mount {user}'s encrypted home folder!".format(user=user))
                return ret

    return 0


def encrypt_user(user, password):
    global _ENCRYPTED_HOME_FOLDERS

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Store the original lock/unlock state.
    is_container_mounted_check = _is_container_mounted()

    # Unlock the container.
    ret = unlock_container(password)
    if ret:
        util.eprint("Could not unlock the encrypted container!")
        return ret

    # Check if the user is already encrypted.
    if os.path.exists(os.path.join(_ENCRYPTED_HOME_FOLDERS, user)):
        print("User is already encrypted!")

        # Restore the original lock/unlock state, and if the original
        # lock/unlock state is unlocked, mount the user's encrypted home folder.
        if not is_container_mounted_check:
            ret = lock_container()
            if ret:
                util.eprint("Could not lock the container again!")
                return ret
        else:
            os.makedirs("/home/" + user, exist_ok=True)
            ret = util.silent_execute([
                "mount", "--bind", os.path.join(_ENCRYPTED_HOME_FOLDERS,
                                                user), "/home/" + user
            ])
            if ret:
                util.eprint(
                    "Could not mount {user}'s encrypted home folder!".format(user=user))
                return ret

        return 0

    util.kill_all_processes_owning_a_folder("/home/" + user)
    ret = util.silent_execute([
        "rm", "-rf",
        os.path.join(_ENCRYPTED_HOME_FOLDERS, user)
    ])
    if ret:
        util.eprint(
            "Could not delete {user}'s empty folder inside the encrypted container!".format(user=user))
        return ret
    try:
        os.makedirs(_ENCRYPTED_HOME_FOLDERS, exist_ok=True)
    except OSError:
        util.eprint(
            "Could not create the main home folder inside the encrypted container!")
        return 1
    ret = util.silent_execute([
        "mv",
        "/home/" + user,
        os.path.join(_ENCRYPTED_HOME_FOLDERS, user)
    ])
    if ret:
        util.eprint(
            "Could not move {user}'s home folder inside the encrypted container!".format(user=user))
        return ret

    # Restore the original lock/unlock state, and if the original
    # lock/unlock state is unlocked, mount the user's encrypted home folder.
    if not is_container_mounted_check:
        # Lock the container.
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the encrypted container again!")
            return ret
    else:
        try:
            os.makedirs("/home/" + user, exist_ok=True)
        except OSError:
            util.eprint(
                "Could not create {user}'s home folder's encryption mount point!".format(user=user))
            return 1
        ret = util.silent_execute([
            "mount", "--bind", os.path.join(_ENCRYPTED_HOME_FOLDERS,
                                            user), "/home/" + user
        ])
        if ret:
            util.eprint(
                "Could not mount {user}'s encrypted home folder!".format(user=user))
            return ret
    return 0


def decrypt_user(user, password):
    global _ENCRYPTED_HOME_FOLDERS

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Store the original lock/unlock state.
    is_container_mounted_check = _is_container_mounted()

    # Unlock the container.
    ret = unlock_container(password)
    if ret:
        util.eprint("Could not unlock the encrypted container!")
        return ret

    # Check if the user is not encrypted.
    if not os.path.exists(os.path.join(_ENCRYPTED_HOME_FOLDERS, user)):
        print("User is not encrypted!")

        # Restore the original lock/unlock state.
        if not is_container_mounted_check:
            ret = lock_container()
            if ret:
                util.eprint("Could not lock the encrypted container again!")
                return ret

        return 0

    # Unmount the user's encrypted home folder.
    if util.is_dir_mounted("/home/" + user):
        util.kill_all_processes_owning_a_folder("/home/" + user)
        ret = util.silent_execute([
            "umount", "/home/" + user
        ])
        if ret:
            util.eprint(
                "Could not unmount {user}'s encrypted home folder!".format(user=user))
        if util.is_dir_mounted("/home/" + user):
            ret = util.silent_execute([
                "umount", "-l", "/home/" + user
            ])
            if ret:
                util.eprint(
                    "Could not lazy unmount {user}'s encrypted home folder!".format(user=user))
                return ret

    # Delete the folder that exists in the main system home folder, and
    # move the user's home folder outside the encrypted container into the main system home folder.
    ret = util.silent_execute([
        "rm", "-rf",
        "/home/" + user
    ])
    if ret:
        util.eprint(
            "Could not delete {user}'s encrypted home folder mount point!".format(user=user))
        return ret
    try:
        os.makedirs("/home", exist_ok=True)
    except OSError:
        util.eprint("Could not create the main system home folder!")
        return 1
    ret = util.silent_execute([
        "mv",
        os.path.join(_ENCRYPTED_HOME_FOLDERS, user),
        "/home/" + user
    ])
    if ret:
        util.eprint(
            "Could not move {user}'s home folder back into the main system home folder!".format(user=user))
        return ret

    # Restore the original lock/unlock state.
    if not is_container_mounted_check:
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the encrypted container again!")
            return ret

    return 0


def decrypt_all_users(password):
    global _ENCRYPTED_HOME_FOLDERS

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Do the same as "decrypt_user", but for all users inside the encrypted container.

    # Store the original lock/unlock state.
    is_container_mounted_check = _is_container_mounted()

    # Unlock the container.
    ret = unlock_container(password)
    if ret:
        util.eprint("Could not unlock the encrypted container!")
        return ret

    if os.path.exists(_ENCRYPTED_HOME_FOLDERS):
        for user in os.listdir(_ENCRYPTED_HOME_FOLDERS):
            # Unmount the user's encrypted home folder.
            if util.is_dir_mounted("/home/" + user):
                util.kill_all_processes_owning_a_folder("/home/" + user)
                ret = util.silent_execute([
                    "umount", "/home/" + user
                ])
                if ret:
                    util.eprint(
                        "Could not unmount {user}'s encrypted home folder!".format(user=user))
                if util.is_dir_mounted("/home/" + user):
                    ret = util.silent_execute([
                        "umount", "-l", "/home/" + user
                    ])
                    if ret:
                        util.eprint(
                            "Could not lazy unmount {user}'s encrypted home folder!".format(user=user))
                        return ret

            # Delete the folder that exists in the main system home folder, and
            # move the user's home folder outside the encrypted container into the main system home folder.
            ret = util.silent_execute([
                "rm", "-rf",
                "/home/" + user
            ])
            if ret:
                util.eprint(
                    "Could not delete {user}'s encrypted home folder mount point!".format(user=user))
                return ret
            try:
                os.makedirs("/home", exist_ok=True)
            except OSError:
                util.eprint("Could not create the main system home folder!")
                return 1
            ret = util.silent_execute([
                "mv",
                os.path.join(_ENCRYPTED_HOME_FOLDERS, user),
                "/home/" + user
            ])
            if ret:
                util.eprint(
                    "Could not move {user}'s home folder back into the main system home folder!".format(user=user))
                return ret

    # Restore the original lock/unlock state.
    if not is_container_mounted_check:
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the encrypted container again!")
            return ret
    return 0


def create_container(container_size, encrypted_swap_size, password):
    global _CONTAINER_LOCATION
    global _ENCRYPTED_SWAP_LOCATION

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Check if the container is not already created.
    if os.path.exists(_CONTAINER_LOCATION):
        print("The container already built!")
        return 0

    # Create the container.
    container_size = int(util.convert_to_bytes(str(container_size)))
    encrypted_swap_size = int(util.convert_to_bytes(str(encrypted_swap_size)))
    total_size = container_size + encrypted_swap_size
    original_proc_visibility = _hide_proc()
    while not original_proc_visibility:
        util.eprint("Could not hide root processes! Trying again...")
        time.sleep(2)
        original_proc_visibility = _hide_proc()
    ret = util.silent_execute([
        "veracrypt", "--text", "--create", "--size", str(total_size),
        "--password", password, "--non-interactive", "--hash", "sha512",
        "--encryption", "AES", "--filesystem", "ext4", "--pim", "0",
        "--volume-type", "normal", _CONTAINER_LOCATION
    ])
    if ret:
        util.eprint("Container creation failed!")
        while not _restore_proc_visibility(original_proc_visibility):
            util.eprint(
                "Could not restore root processes visibility! Trying again...")
            time.sleep(2)
        return ret
    while not _restore_proc_visibility(original_proc_visibility):
        util.eprint(
            "Could not restore root processes visibility! Trying again...")
        time.sleep(2)

    # Create the encrypted swap.
    if encrypted_swap_size > 0:
        ret = unlock_container(password)
        if ret:
            util.eprint("Could not unlock the encrypted container!")
            return ret
        ret = util.silent_execute([
            "fallocate", "-l", str(encrypted_swap_size), _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint("Could not create the encrypted swap file!")
            return ret
        ret = util.silent_execute([
            "mkswap", _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint(
                "Could not create the swap system inside the encrypted swap file!")
            return ret
        ret = util.silent_execute([
            "chmod", "0600", _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint(
                "Could not change the encrypted swap file's mode to \"0600\"!")
            return ret
        ret = util.silent_execute([
            "chown", "root", _ENCRYPTED_SWAP_LOCATION
        ])
        if ret:
            util.eprint(
                "Could not change the encrypted swap file's ownership to root!")
            return ret
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the encrypted container again!")
            return ret
    return 0


def destroy_container():
    global _CONTAINER_LOCATION

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    # Check if the container is created.
    if not os.path.exists(_CONTAINER_LOCATION):
        print("The container is not built yet!")
        return 0

    # Lock the container first.
    ret = lock_container()
    if ret:
        util.eprint("Could not lock the container!")
        return ret

    # Then, destroy the container.
    try:
        os.remove(_CONTAINER_LOCATION)
    except OSError:
        util.eprint("Could not remove the container!")
        return 1
    return 0


def resize_container(container_size, encrypted_swap_size, password):
    global _CONTAINER_LOCATION
    global _ENCRYPTED_HOME_FOLDERS
    global _ENCRYPTED_SWAP_LOCATION

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    container_size = int(util.convert_to_bytes(str(container_size)))
    encrypted_swap_size = int(util.convert_to_bytes(str(encrypted_swap_size)))
    total_size = container_size + encrypted_swap_size

    # Resize the total container size if the total size is changed.
    if total_size != util.get_file_size_in_bytes(_CONTAINER_LOCATION):
        # Store the original lock/unlock state.
        is_container_mounted_check = _is_container_mounted()

        # Unlock the container.
        ret = unlock_container(password)
        if ret:
            util.eprint("Could not unlock the encrypted container!")
            return ret

        # List the currently encrypted users.
        users = list()
        if os.path.exists(_ENCRYPTED_HOME_FOLDERS):
            users = os.listdir(_ENCRYPTED_HOME_FOLDERS)

        # Decrypt all users.
        ret = decrypt_all_users(password)
        if ret:
            util.eprint("Could not decrypt all users!")
            return ret

        # Lock and delete the original container.
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the old container!")
            return ret
        ret = destroy_container()
        if ret:
            util.eprint("Could not destroy the old container!")
            return ret

        # Create a new container with the new sizes.
        ret = create_container(str(container_size), str(
            encrypted_swap_size), password)
        if ret:
            util.eprint("Could not create the new container!")
            return ret

        for user in users:
            ret = encrypt_user(user, password)
            if ret:
                util.eprint(
                    "Could not encrypt {user}'s home directory again!".format(user=user))
                return ret

        # Restore the lock/unlock state of the container.
        if is_container_mounted_check:
            ret = unlock_container(password)
            if ret:
                util.eprint("Could not unlock the new container!")
                return ret

    # Check if the swap size is different.
    else:
        # Store the original lock/unlock state.
        is_container_mounted_check = _is_container_mounted()

        # Unlock the container.
        ret = unlock_container(password)
        if ret:
            util.eprint("Could not unlock the encrypted container!")
            return ret

        # Resize the swap image if the new size is different from the original size.
        current_swap_size = 0
        if os.path.exists(_ENCRYPTED_SWAP_LOCATION):
            current_swap_size = util.get_file_size_in_bytes(
                _ENCRYPTED_SWAP_LOCATION)
        if current_swap_size != encrypted_swap_size:
            if os.path.exists(_ENCRYPTED_SWAP_LOCATION):
                util.silent_execute([
                    "swapon", _ENCRYPTED_SWAP_LOCATION
                ])
                ret = util.silent_execute([
                    "swapoff", _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint("Could not swap off the encrypted swap file!")
                    return ret
                try:
                    os.remove(_ENCRYPTED_SWAP_LOCATION)
                except OSError:
                    util.eprint("Could not remove the old swap file!")
                    return 1
            if encrypted_swap_size > 0:
                ret = util.silent_execute([
                    "fallocate", "-l", str(
                        encrypted_swap_size), _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint("Could not create the encrypted swap file!")
                    return ret
                ret = util.silent_execute([
                    "mkswap", _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint(
                        "Could not create the swap system inside the encrypted swap file!")
                    return ret
                ret = util.silent_execute([
                    "chmod", "0600", _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint(
                        "Could not change the encrypted swap file's mode to \"0600\"!")
                    return ret
                ret = util.silent_execute([
                    "chown", "root", _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint(
                        "Could not change the encrypted swap file's ownership to root!")
                    return ret
                util.silent_execute([
                    "swapoff", _ENCRYPTED_SWAP_LOCATION
                ])
                ret = util.silent_execute([
                    "swapon", _ENCRYPTED_SWAP_LOCATION
                ])
                if ret:
                    util.eprint("Could not swap on the encrypted swap file!")
                    return ret
        else:
            print("Nothing has been resized!")

        # Restore the lock/unlock state of the container.
        if is_container_mounted_check:
            ret = unlock_container(password)
            if ret:
                util.eprint("Could not unlock the encrypted container again!")
                return ret

    return 0


def change_container_password(old_password, new_password):
    global _CONTAINER_LOCATION

    # Check if the user is not root.
    if os.geteuid() != 0:
        util.eprint("The utility must be running as root!")
        return 1

    if old_password == new_password:
        print("Password is not changed!")
        return 0

    is_container_mounted_check = _is_container_mounted()
    ret = unlock_container(old_password)
    if ret:
        util.eprint(
            "Could not unlock the encrypted container with the old password!")
        return ret

    original_proc_visibility = _hide_proc()
    while not original_proc_visibility:
        util.eprint("Could not hide root processes! Trying again...")
        time.sleep(2)
        original_proc_visibility = _hide_proc()
    ret = util.silent_execute([
        "veracrypt", "--text", "--non-interactive", "--keyfiles=", "--pim", "0",
        "--change", "--password", old_password, "--new-password", new_password, _CONTAINER_LOCATION
    ])
    if ret:
        util.eprint("Could not change the container's password!")
        while not _restore_proc_visibility(original_proc_visibility):
            util.eprint(
                "Could not restore root processes visibility! Trying again...")
            time.sleep(2)
        return ret
    while not _restore_proc_visibility(original_proc_visibility):
        util.eprint(
            "Could not restore root processes visibility! Trying again...")
        time.sleep(2)

    if not is_container_mounted_check:
        ret = lock_container()
        if ret:
            util.eprint("Could not lock the container again!")
            return ret

    return ret
