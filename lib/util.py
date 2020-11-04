import getpass
import sys
import shutil
import os
import stat
import subprocess


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def getpass_verify(password1_msg="Password: ", password2_msg="Verify password: ", error_msg="Passwords do not match!"):
    password1 = getpass.getpass(password1_msg)
    password2 = getpass.getpass(password2_msg)
    if password1 == password2:
        return password1
    else:
        eprint(error_msg)
        return None


def is_dir_mounted(to_test_dir):
    with open(os.devnull, "w") as fd:
        p = subprocess.Popen([
            "findmnt", to_test_dir
        ], stdout=fd, stderr=fd)
        return p.wait() == 0


def convert_to_bytes(to_convert_size, return_zero_on_error=True):
    to_convert_size = str(to_convert_size).strip()
    try:
        # Check if it is already in bytes (i.e. without a suffix).
        return str(int(to_convert_size))
    except ValueError:
        # Get the float number part.
        number_str = ""
        i = 0
        while i < len(to_convert_size):
            try:
                number_str += str(int(to_convert_size[i]))
            except ValueError:
                if to_convert_size[i] == ".":
                    number_str += to_convert_size[i]
                else:
                    break
            i += 1
        if not number_str:
            if return_zero_on_error:
                return str(0)
            else:
                raise ValueError("Cannot convert to bytes.")
        number_float = 0
        try:
            number_float = float(number_str)
        except ValueError:
            if return_zero_on_error:
                return str(0)
            else:
                raise ValueError("Cannot convert to bytes.")

        # Get the suffix. Supported suffixes are K or KB (for kilobytes),
        # M or MB (for megabytes), G or GB (for gigabytes), and T or TB (for
        # terabytes).
        if i < len(to_convert_size) - 2 or i > len(to_convert_size) - 1:
            return str(0)
        if to_convert_size[i].lower() == "k" and\
                ((i == len(to_convert_size) - 1) or ((i == len(to_convert_size) - 2) and (to_convert_size[i + 1].lower() == "b"))):
            return str(round(number_float * 1024.0))
        elif to_convert_size[i].lower() == "m" and\
                ((i == len(to_convert_size) - 1) or ((i == len(to_convert_size) - 2) and (to_convert_size[i + 1].lower() == "b"))):
            return str(round(number_float * 1024.0 * 1024.0))
        elif to_convert_size[i].lower() == "g" and\
                ((i == len(to_convert_size) - 1) or ((i == len(to_convert_size) - 2) and (to_convert_size[i + 1].lower() == "b"))):
            return str(round(number_float * 1024.0 * 1024.0 * 1024.0))
        elif to_convert_size[i].lower() == "t" and\
                ((i == len(to_convert_size) - 1) or ((i == len(to_convert_size) - 2) and (to_convert_size[i + 1].lower() == "b"))):
            return str(round(number_float * 1024.0 * 1024.0 * 1024.0 * 1024.0))
        else:
            if return_zero_on_error:
                return str(0)
            else:
                raise ValueError("Cannot convert to bytes.")


def get_file_size_in_bytes(file_path):
    return int(subprocess.check_output([
        "du", "-sb", file_path
    ]).decode("UTF-8").strip().split()[0])


def silent_execute(cmd):
    with open(os.devnull, "w") as fd:
        p = subprocess.Popen(cmd, stdout=fd, stderr=fd)
        return p.wait()


def kill_all_processes_owning_a_folder(folder):
    try:
        processes = [process.strip() for process in subprocess.check_output(
            ["lsof", "-t", folder]).decode("UTF-8").split(os.linesep) if process.strip()]
        silent_execute(["kill", "-9"] + processes)
    except subprocess.CalledProcessError:
        pass
