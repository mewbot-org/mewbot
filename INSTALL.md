# Mewbot Installation and Usage Guide

Last Updated: 8/16/2021

This guide servers for correct installation of required services for the Mewbot Application to work properly and with as few complications as possible.  Due to variations in host structure and unforseeable issues, it is likely that some issues may arise during the setup of this guide.  Many, if not all, dependent services should be running in an isolated Docker container if possible to minimize such issues, however this guide will detail the setup of a few services that are not running in a Docker container at this date.

There are two parts to this guide.  The first part details the initial setup of Mewbot, directories, services and applications for proper usage, and the second part details the proper startup procedure in the event of a hardware reboot.  Do NOT follow the instructions in the first part unless you are certain that you are on bare hardware and that nothing has been set up.  Improper instruction following may lead to issues later on down the line, or in worst case scenario, data loss.  Please have your developer with the most Linux experience follow this guide to minimize future issues.

## Mewbot Installation and Usage Guide - First Time Setup

As with all setups, here are a few warnings before you proceed with the First Time Setup:

- Never should any piece of code be run as a root user.
- Never disable the firewall that is configured and enabled for your device.
- User passwords should be changed and renewed periodically.
- For Secure Shell (SSH) Authentication, password authentication must be disabled and only allow pubkey login.  SSH shells should not be able to log into root account.
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

1. Install pre-requisite software.
    1. At the writing of this guide, the current requisites are Python 3.9, Git, Docker, Mongo and Tmux.  Please refer to each software's installation instructions to get started.
2. After installing pre-requisite software, continue by pulling this repository to the hosting device and setting up Git to track correctly.  Replace `production` with the currently tracking production branch.  For example, if your master branch currently is `clustered`, replace `production` with `clustered`.  For simplicity, we will stick to `production`.
    1. Create a folder to contain the Mewbot Application.  In this guide, we will use the directory `~/production` under the logged in, non-root sudoer user.
    2. `cd` into the newly created folder, then initialize an empty Git repository with `git init`.
    3. Add this repository as a git remote: `git remote add origin https://github.com/mewbot-dyl/mewbot`.
    4. Pull `origin/production` to locally-checked out `master` branch: `git pull origin production`.
    5. Set currently checked out branch to track from `origin/production`: `git branch --set-upstream-to=origin/production master`.
3. Restore backups from previous hosting devices.
    1. Please refer to the restore guides located at the end of this set up guide.  The instructions you follow may depend on the backup type that you have.
4. Initialize environment files.
    1. Refer to `env/SETUP.md` for instructions regarding this step.
5. Install Mewbot Bot Application pip libraries.
    1. Ensure your current working directory is `~/production`.
    2. Run `pip install -r references/requirements.txt`
    3. It is possible that due to recent changes to Pip's dependency resolver that some libraries may fail to install.  In such cases, run the command `pip install -r references/requirements.txt --use-deprecated=legacy-resolver`.
6. Start docker services
    1. Ensure your current working directory is `~/production`.
    2. Run `sudo docker-compose up`.  This command may take a few minutes as it pulls the needed images from Docker Hub.
    3. Check initial set up logs while this is running to ensure no services encounter errors while initializing.  If none do, you can Ctrl + C the process.
    4. Start Docker services in detached mode: `sudo docker-compose up -d`.
> If at the time of following this guide that the Mewbot Callbacks application and Mongo Data Source are not yet running in a Docker container, follow the section later in this guide before continuing.
7. Create `/etc/systemd/system/mewbot.service`.
    1. Refer to `references/mewbot.service` for a base template for this file.  Based upon your current logged in user and your production environment folder name, you may need to edit the path.
8. Run `sudo systemctl daemon-reload` to reload SystemCTL files.
9. Start the Mewbot Application with `sudo systemctl start mewbot`.
10. Create cron job for data source backups.
    1. Determine the path to `references/backup.sh`.  For the purpose of this guide, we will assume the path `/home/ubuntu/production/references/backup.sh`.  Please also ensure that the relevant locations `/home/ubuntu/backups/mongo-backups` and `/home/ubuntu/backups/postgres-backups` exist.
    2. Run `crontab -e` to edit the crontab file for the current logged in user.
    3. Add the following line to the bottom of the Crontab file: `01 01 * * * /home/ubuntu/production/references/backup.sh`.  This will run the backup shell file every day at 1:01 AM.

### Mewbot Installation and Usage Guide - Mongo and Callbacks Setup Guide

In the event that the Mongo Data Source (and as a result, Mewbot Callbacks application) are not running in a Docker container, they will require extra set up.  Do not follow the instructions of restoring from a backup of Mongo in a later section if you are following this guide.  Instead, follow the instructions listed here.

1. Obtain the latest backup dump that has been created using the backup script from your previous hosting device.
2. Locate the backup dump (directory hereafter referred to as `dump`), and with Mongo installed on your system, run `mongorestore dump/`.
3. Create and initialize users using credentials in `env/mongo.env` using the guide located at https://docs.mongodb.com/manual/tutorial/enable-authentication/.
4. Stop Docker Container running Mewbot Callbacks:
    1. `cd` to `~/production`.
    2. Run `sudo docker-compose stop mewbot-callbacks`.
5. To set up the Mewbot Callbacks application:
    1. Start a tmux session `tmux new -s callbacks`.
    2. `cd` to `~/production/callbacks`
    3. Run `pip install -r requirements.txt`
    4. It is possible that due to recent changes to Pip's dependency resolver that some libraries may fail to install.  In such cases, run the command `pip install -r requirements.txt --use-deprecated=legacy-resolver`.
    5. `cd` to `~/production/callbacks/src`
    6. Export the following Environment Values using the credentials located in the `env/` directory at the root of this repository:
        - `MTOKEN`
        - `DATABASE_URL`
        - `FATESLIST`
        - `DBL`
        - `TOPGGVERIFY`
    7. Export the Environment Value `MONGO_URL` to the proper connection schema.  This likely will use one similar to that located in `env/mongo.env`, however the host IP address will need to be changed to `localhost`.
    8. Run script using `python3.8 main.py`
