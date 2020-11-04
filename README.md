# Home Encryption Utility for Linux Operating Systems Based on VeraCrypt 1.24+

### Requirements

- VeraCrypt version 1.24 or above.
- Python 3.7+.
- The following set of commands (most of them are already available on a default Linux install):
  - `mount`/`umount` commands.
  - `swapon`/`swapoff` commands.
  - `rm`/`mv` commands (used these commands instead of portable Python alternatives, as these commands support cross-filesystem movement/deletion while retatining the ownership).
  - `fallocate` command.
  - `mkswap` command.
  - `chmod`/`chown` commands.
  - `findmnt` command.
  - `lsof` command.
  - `kill` command.
  - `du` command.

### Install/Uninstall

- Set `HOME_ENCRYPTION_UTIL_INSTALL` and `HOME_ENCRYPTION_UTIL_INSTALL_PREFIX` with the whole project install and the symlink `home-encryption-util`->`home-encryption-util.sh` inside the `bin` folder in the preferred prefix, respectively. If you do not set them, they will be assigned the values of `/opt/home-encryption-util` and `/usr`, respectively.
- Run `install.sh`/`uninstall.sh` to install/uninstall the utility.

### How to use

After installing the utility, run `home-encryption-util help` to print the how-to help message.

### Recommended usage.

- Create a seperate account with super user access.
- Use that account on reboot to decrypt the encrypted container containing the encrypted home folders.
- Make sure you read the warnings in the `help` message in the utility.

### TODO

- Add config file to set the encryption settings on container creation, such as the hash algorithm to be used or the PIM level.
- Add the following commands:
  - `listencryptedusers`: List currently encrypted users' home folders.
  - `isuserencrypted`: Show whether a user is currently encrypted or not.
  - `sizeinfo`: Show the container's size and the swap memory's size in use.
