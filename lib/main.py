import sys
import os
import getpass
import container_manager
import util


def get_help_text():
    # autopep8: off
    return "Home encryption utility based on VeraCrypt for Linux operating systems.{linesep}{linesep}"\
           "Usage: {cmd} command [argument1 argument2 ...]{linesep}{linesep}"\
           "Where:{linesep}"\
           "    - command: The command to do.{linesep}"\
           "    - argumentX: The command argument.{linesep}{linesep}"\
           "Commands can be one of the following:{linesep}"\
           "    - help: Print this help message and exit cleanly.{linesep}"\
           "    - unlockcontainer [password]: This command will unlock the container. If \"password\" argument is not provided"\
                                            " for the password, a password text prompt will be shown instead to unlock the container.{linesep}"\
           "    - lockcontainer: This command will lock the container.{linesep}"\
           "    - encryptuser user [password]: Encrypt a user \"user\". If \"password\" argument is not provided for the password,"\
                                             " a password text prompt will be shown instead to unlock the container.{linesep}"\
           "    - decryptuser user [password]: Decrypt a user \"user\". If \"password\" argument is not provided for the password,"\
                                             " a password text prompt will be shown instead to unlock the container.{linesep}"\
           "    - decryptallusers [password]: Decrypt all users. If \"password\" argument is not provided for the password,"\
                                            " a password text prompt will be shown instead to unlock the container.{linesep}"\
           "    - createcontainer containersize swapsize [password]: Create the container with size \"containersize\" and"\
                                                                   " encrypted swap file with size \"swapsize\". Sizes"\
                                                                   " can be postfixed with (K/k)[(B/b)] for kilobytes (e.g. KB),"\
                                                                   " (M/m)[(B/b)] for megabytes (e.g. MB), (G/g)[(B/b)] for"\
                                                                   " gigabytes (e.g. GB), or (T/t)[(B/b)] for terabytes (e.g. TB)."\
                                                                   " Postfixes have to be stuck right after the number (e.g. 1GB)."\
                                                                   " If a postfix is used, the number can can be a positive float number."\
                                                                   " If a postfix is not used, the number is assumed to be in bytes,"\
                                                                   " and it can only be a positive integer number. However,"\
                                                                   " the only exception to the positive float number and"\
                                                                   " positive integer number above is the size of the"\
                                                                   " encrypted swap file, which can be 0 if you want to"\
                                                                   " delete it. The total size of the container is equals to:"\
                                                                   " \"containersize\" + \"swapsize\". If \"password\" argument"\
                                                                   " is not provided for the password, two password text prompts will"\
                                                                   " be shown to enter and verify the passwords instead to set the"\
                                                                   " password.{linesep}"\
           "    - resizecontainer containersize swapsize [password]: Resize the container with size \"containersize\" and"\
                                                                   " encrypted swap file with size \"swapsize\". Sizes"\
                                                                   " can be postfixed with (K/k)[(B/b)] for kilobytes (e.g. KB),"\
                                                                   " (M/m)[(B/b)] for megabytes (e.g. MB), (G/g)[(B/b)] for"\
                                                                   " gigabytes (e.g. GB), or (T/t)[(B/b)] for terabytes (e.g. TB)."\
                                                                   " Postfixes have to be stuck right after the number (e.g. 1GB)."\
                                                                   " If a postfix is used, the number can can be a positive float number."\
                                                                   " If a postfix is not used, the number is assumed to be in bytes,"\
                                                                   " and it can only be a positive integer number. However,"\
                                                                   " the only exception to the positive float number and"\
                                                                   " positive integer number above is the size of the"\
                                                                   " encrypted swap file, which can be 0 if you want to"\
                                                                   " delete it. The total size of the container is equals to:"\
                                                                   " \"containersize\" + \"swapsize\". If \"password\" argument"\
                                                                   " is not provided for the password, a password text prompt will"\
                                                                   " be shown instead to unlock the old container. If you are intended"\
                                                                   " to only resize the encrypted swap file but keep the total size"\
                                                                   " exactly the same as the current container, it is better to recalculate the"\
                                                                   " the following ratio again, and make it equal to the original total size:"\
                                                                   " \"containersize\" + \"swapsize\".{linesep}"\
           "    - destroycontainer: Destroy the container. WARNING: Make sure you decrypt all encrypted users if you do not want to lose encrypted"\
                                                                  " users' data.{linesep}"\
           "    - changecontainerpw [oldpw [newpw]]: Change the container's password. If any of \"oldpw\", for the old password, or \"newpw\","\
                                                   " for the new password, is not provided, a password text propmt will be provided to"\
                                                   " to enter the old password for the old password, or two password text prompts will be"\
                                                   " provided to enter and verify the new password, to set the new container password.{linesep}{linesep}"\
           "Extra WARNINGS:{linesep}"\
           "    - All commands must be done while the computer is attended and they must all finish succesfully before shutdown, or you might risk"\
                " losing your data, or having your data unencrypted.{linesep}"\
           "    - Commands cannot be done in parallel.{linesep}"\
           "    - Once the container is unlocked, you must not edit the swap memory manually, as this will cause issues to backup/restore the"\
                " original swap memory state.{linesep}"\
           .format(
               cmd="home-encryption-util", linesep=os.linesep
           )
    # autopep8: on


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "lockcontainer":
        return container_manager.lock_container()
    elif (len(sys.argv) == 3 or len(sys.argv) == 2) and sys.argv[1] == "unlockcontainer":
        password = None
        if len(sys.argv) == 3:
            password = sys.argv[2]
        else:
            password = getpass.getpass()
        return container_manager.unlock_container(password)
    elif (len(sys.argv) == 4 or len(sys.argv) == 3) and sys.argv[1] == "encryptuser":
        password = None
        if len(sys.argv) == 4:
            password = sys.argv[3]
        else:
            password = getpass.getpass()
        return container_manager.encrypt_user(sys.argv[2], password)
    elif (len(sys.argv) == 4 or len(sys.argv) == 3) and sys.argv[1] == "decryptuser":
        password = None
        if len(sys.argv) == 4:
            password = sys.argv[3]
        else:
            password = getpass.getpass()
        return container_manager.decrypt_user(sys.argv[2], password)
    elif (len(sys.argv) == 3 or len(sys.argv) == 2) and sys.argv[1] == "decryptallusers":
        password = None
        if len(sys.argv) == 3:
            password = sys.argv[2]
        else:
            password = getpass.getpass()
        return container_manager.decrypt_all_users(password)
    elif (len(sys.argv) == 5 or len(sys.argv) == 4) and sys.argv[1] == "createcontainer":
        password = None
        if len(sys.argv) == 5:
            password = sys.argv[4]
        else:
            password = util.getpass_verify()
            if not password:
                return 1
        return container_manager.create_container(sys.argv[2], sys.argv[3], password)
    elif len(sys.argv) == 2 and sys.argv[1] == "destroycontainer":
        return container_manager.destroy_container()
    elif (len(sys.argv) == 5 or len(sys.argv) == 4) and sys.argv[1] == "resizecontainer":
        password = None
        if len(sys.argv) == 5:
            password = sys.argv[4]
        else:
            password = getpass.getpass()
        return container_manager.resize_container(sys.argv[2], sys.argv[3], password)
    elif (len(sys.argv) == 4 or len(sys.argv) == 3 or len(sys.argv) == 2) and sys.argv[1] == "changecontainerpw":
        old_password = None
        new_password = None
        if len(sys.argv) == 4:
            old_password = sys.argv[2]
            new_password = sys.argv[3]
        elif len(sys.argv) == 3:
            old_password = sys.argv[2]
            new_password = util.getpass_verify(
                password1_msg="New password: ", password2_msg="Verify new password: ")
            if not new_password:
                return 1
        elif len(sys.argv) == 2:
            old_password = getpass.getpass(prompt="Old password: ")
            new_password = util.getpass_verify(
                password1_msg="New password: ", password2_msg="Verify new password: ")
            if not new_password:
                return 1
        return container_manager.change_container_password(old_password, new_password)
    elif len(sys.argv) == 2 and sys.argv[1] == "help":
        print(get_help_text())
        return 0, True
    else:
        util.eprint("Wrong usage. See the help message below on how to use this utility.{linesep}".format(
            linesep=os.linesep))
        util.eprint(get_help_text())
        return 1, True


if __name__ == "__main__":
    ret = main()
    if type(ret) == tuple:
        os._exit(ret[0])
    else:
        if not ret:
            print("The command succeeded!")
        else:
            util.eprint("The command failed!")
        os._exit(ret)
