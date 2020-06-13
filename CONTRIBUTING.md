## Contributing
### Prerequisites

If you plan on testing any functionality involving the Spotify API, you need to have a [registered App with Spotify][spotifydev-url] in order to get a Client ID and Client Secret.

* Python 3 and Pip
    * Linux
        ```sh
        sudo apt update && sudo apt upgrade
        sudo apt install python3 python3-pip
        ```
    * Windows
        * [Download and Install the latest Python 3 release][windows-python-url]
            * IMPORTANT: When installing, please check "Add Python 3.x to PATH"
            * (Optional) When installing, select "Disable path length limit" (this may resolve some bugs)

### Installation
 
1. Fork the Repository on GitHub
    * It is recommended that you fork the repository so you can push changes and submit pull requests.

2. Clone the forked Repository locally
    ```sh
    git clone https://github.com/YOUR-USERNAME/gifsync.git
    cd gifsync
    ```

2. (Optional) Create a Python virtual environment
    * Linux
        ```sh
        sudo apt update
        sudo apt install python3-venv
        python3 -m venv venv
        source venv/bin/activate
        ```
    * Windows
        ```sh
        python -m venv venv
        venv\Scripts\activate.bat
        ```

3. Install required modules
    * Linux
        ```sh
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
        ```
    * Windows
        * Replace "python3" with "python" in the Linux commands above

4. Run the server
    * Linux
        ```sh
        python3 -m run
        ```
    * Windows
        * Replace "python3" with "python" in the Linux commands above

### Making Changes
1. Create your Feature Branch (`git checkout -b feature/SomeFeature`)
2. Make some changes and stage them (`git add .`)
3. Commit your Changes (`git commit -m 'Add some Feature'`)
    - If you make multiple commits, please [squash them][squash-url] into a single commit before Pushing or opening a Pull request
4. Push to the Branch (`git push origin feature/SomeFeature`)
5. Open a Pull Request on GitHub

### Additional Information
You can use your favorite Python IDE, however I recommend using [PyCharm][pycharm-url] as it allows for built-in VCS support and virtual environments.

[spotifydev-url]: https://developer.spotify.com/dashboard/login
[windows-python-url]: https://www.python.org/downloads/windows/
[squash-url]: https://stackoverflow.com/questions/5189560/squash-my-last-x-commits-together-using-git
[pycharm-url]: https://www.jetbrains.com/pycharm/
