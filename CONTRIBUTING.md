# Contributing

> WARNING: These docs may be outdated!

There are two main ways to start developing and contributing to GifSync: **Docker Compose** (all dependencies and python
requirements are hosted in a container), or a **Local Build** (dependencies and python must be installed locally).

All Linux commands assume you are running a debian-based system. All Windows commands assume you are running Windows 10.

<!-- TABLE OF CONTENTS -->

## Table of Contents

- [Docker Compose](#docker-compose)
  - [Prerequisites](#prerequisites-docker)
  - [Environment Setup](#environment-setup-docker)
- [Local Build](#local-build)
  - [Prerequisites](#prerequisites-local)
  - [Environment Setup](#environment-setup-local)
- [Making Changes](#making-changes)
- [Additional Information](#additional-information)

## Docker Compose

### Prerequisites (Docker)

- Docker and Docker Compose

  - Linux

    ```sh
    # DOCKER
    sudo apt update && sudo apt upgrade
    sudo apt install apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt update && sudo apt install docker-ce
    sudo usermod -aG docker ${USER}
    # Restart your computer through GUI or use "sudo shutdown -r now"

    # Verify docker is installed
    docker --version

    # DOCKER-COMPOSE
    # Confirm that the release number for docker-compose matches
    # the latest release at https://github.com/docker/compose/releases
    sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # Verify docker-compose is installed
    docker-compose --version
    ```

  - Windows
    - Docker does not natively run on windows and will require installing the Linux Kernel Update Package provided by
      Microsoft, enabling Virtualization, and potentially enabling Hyper-V.
      The setup for Docker Desktop varies based on if you are running [Windows 10 Home][docker-windows-home-url] or
      [Windows 10 Pro/Education/Enterprise][docker-windows-url]

### Environment Setup (Docker)

1. Fork the Repository on GitHub

   - It is recommended that you fork the repository so you can push changes and submit pull requests.

2. Clone the forked Repository locally

   ```sh
   git clone https://github.com/YOUR-USERNAME/gifsync.git
   cd gifsync
   ```

3. Create two new files called **web.env** and **db.env** within the project's root directory.

   - Populate **db.env** with the following:
     ```
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=devpassword
     ```
   - **web.env** must have `CLIENT_ID` and `CLIENT_SECRET` defined (see
     [Additional Information](#additional-information) for getting a Spotify Client & Secret ID). Populate **web.env**
     with the following:
     `   CLIENT_ID=your_spotify_client_id
 CLIENT_SECRET=your_spotify_client_secret
 DATABASE_URL=postgresql://postgres:devpassword@db:5432/postgres`
   - Optional values for **web.env** include:
     - `FLASK_ENV` - recommended value: `development`
     - `SECRET_KEY` - not necessary to set, defaults to `devkey`
     - `PORT` - if set, you **MUST** change the port definition within the `docker-compose.yml` file to match

4. Run `docker-compose up --build -d` (omit the "-d" flag if you wish to keep the containers attached to the terminal,
   useful for debugging)
   _ To view the site, open a browser and go to `localhost:8000` or to the port you've specified in `web.env`
   _ Changes made to **HTML** and **CSS** will be reflected automatically after waiting approx. 10-15 seconds. \* Changes to **code** will **NOT** be reflected automatically. Restart the server with `docker-compose down`, then
   `docker-compose up --build -d`.

## Local Build

### Prerequisites (Local)

- Python 3 and Pip
  - Linux
    ```sh
    sudo apt update && sudo apt upgrade
    sudo apt install python3 python3-pip
    ```
  - Windows
    - [Download and Install the latest Python 3 release][windows-python-url]
      - IMPORTANT: When installing, please check "Add Python 3.x to PATH"
      - (Optional) When installing, select "Disable path length limit" (this may resolve some bugs)
- PostgreSQL / Psql
  - Docker
    - I highly recommend using Docker for PostgreSQL. Please see the [Docker Prerequisites](#prerequisites-docker)
      section for help setting up Docker, then proceed with the next steps.
    - Follow steps 1 & 2 in [Environment Setup (Local)](#environment-setup-local), then run the following command:
      ```sh
      docker-compose -f docker-compose.postgres.yml up --build -d
      ```
    - Open a web browser and go to `localhost:8080`. Within the Adminer console, select/enter the following:
      - System: PostgreSQL
      - Server: db
      - Username: postgres
      - Password: devpassword
      - Database: postgres
    - Click on "Import" near the left-hand side, and under "File upload" select the file `db_template.sql`.
      Execute the chosen file. You now have a test database that is available for the app to use, and a GUI to
      interact with the database. If you wish to use the command line, enter `docker exec -it gifsync_db_1 bash` and
      once you are in the container's terminal, enter `psql -U postgres`.
  - Linux
    - Follow steps 1 & 2 in [Environment Setup (Local)](#environment-setup-local), then run the following commands:
    ```sh
    sudo apt update && sudo apt install postgresql
    # If you don't set the password to "devpassword", you will need to modify the password used in the code,
    # or utilize environment variables and define a port in web.env
    # It is recommended that you set a strong password when running postgres locally on your machine like this.
    sudo passwd postgres
    sudo su - postgres
    psql -U postgres -d postgres -a -f /absolute/path/to/project/db_template.sql
    ```
  - Windows
    - Follow steps 1 & 2 in [Environment Setup (Local)](#environment-setup-local) to get the `db_template.sql` file
    - [Download][postgres-windows-url] and install PostgreSQL and PgAdmin installer
    - Use PgAdmin to run the `db_template.sql` file

### Environment Setup (Local)

1. Fork the Repository on GitHub

   - It is recommended that you fork the repository so you can push changes and submit pull requests.

2. Clone the forked Repository locally

   ```sh
   git clone https://github.com/YOUR-USERNAME/gifsync.git
   cd gifsync
   ```

3. (Optional) Create a Python virtual environment

   - Linux
     ```sh
     sudo apt update
     sudo apt install python3-venv
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows
     ```sh
     python -m venv venv
     venv\Scripts\activate.bat
     ```

4. Install required modules

   - Linux
     ```sh
     python3 -m pip install --upgrade pip
     python3 -m pip install -r requirements.txt
     ```
   - Windows
     - Replace "python3" with "python" in the Linux commands above

5. Create two new files called **web.env** and **db.env** within the project's root directory.

   - Populate **db.env** with the following:
     ```
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=devpassword
     ```
   - **web.env** must have `CLIENT_ID` and `CLIENT_SECRET` defined (see
     [Additional Information](#additional-information) for getting a Spotify Client & Secret ID). Populate **web.env**
     with the following:
     `   CLIENT_ID=your_spotify_client_id
 CLIENT_SECRET=your_spotify_client_secret`
   - Optional values for **web.env** include:
     - `FLASK_ENV` - not necessary to set, defaults to: `development`
     - `DATABASE_URL` - if you are connecting to an external database or have defined a different user/password than
       what is in **db.env** file above
     - `SECRET_KEY` - not necessary to set, defaults to `devkey`
     - `PORT` - not necessary to set, defaults to `8000`

6. Run the server
   - Linux
     ```sh
     python3 -m run
     ```
   - Windows
     - Replace "python3" with "python" in the Linux commands above
   - To view the site, open a browser and go to localhost:PORT (PORT defaults to 5000 if not set as an environment
     variable or modified in `run.py`)

## Making Changes

1. Create your Feature Branch (`git checkout -b feature/SomeFeature`)
2. Make some changes and stage them (`git add .`)
3. Commit your Changes (`git commit -m 'Add some Feature'`)
   - If you make multiple commits, please [squash them][squash-url] into a single commit before Pushing or opening a Pull request
4. Push to the Branch (`git push origin feature/SomeFeature`)
5. Open a Pull Request on GitHub

## Additional Information

- You need to have a [registered App with Spotify][spotifydev-url] in order to get a Client ID and Client Secret.
- You can use your favorite Python IDE, however I recommend using [PyCharm][pycharm-url] as it allows for built-in VCS
  support and virtual environments, and an awesome plugin (EnvFile) for adding environment variables at runtime.
- When making changes to HTML/CSS, browsers will cache the files for faster load times so you may not see your changes
  if you refresh the page. To fix this, do a Hard Reload of the page. In Chrome/Firefox the command is `Ctrl+Shift+R`, in
  Edge/IE the command is `Ctrl+F5`, and in Safari the command is hold `Shift` and click the Refresh button.
- Keep your fork up-to-date by adding this repository as an upstream:
  - `git remote add upstream https://github.com/Septem151/gifsync.git`
  - Fetching and merging diffs:
    ```sh
    git fetch upstream
    git checkout some-local-branch    # some-local-branch is the local branch you want to merge updates into
    git merge upstream/some-branch    # some-branch is the branch from this repository you want to merge updates from
    ```

[spotifydev-url]: https://developer.spotify.com/dashboard/login
[windows-python-url]: https://www.python.org/downloads/windows/
[squash-url]: https://stackoverflow.com/questions/5189560/squash-my-last-x-commits-together-using-git
[pycharm-url]: https://www.jetbrains.com/pycharm/
[docker-windows-home-url]: https://docs.docker.com/docker-for-windows/install-windows-home/
[docker-windows-url]: https://docs.docker.com/docker-for-windows/install/
[postgres-windows-url]: https://www.postgresql.org/download/windows/
