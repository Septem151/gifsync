## Contributing
### Prerequisites

If you plan on testing any functionality involving the Spotify API, you need to have a [registered App with Spotify][spotifydev-url] in order to get a Client ID and Client Secret.

* Python 3 and Pip
    ```sh
    sudo apt update && sudo apt upgrade
    sudo apt install python3 python3-pip
    python3 -m pip install --upgrade pip
    ```

### Installation
 
1. Fork the Repository on GitHub
    * It is recommended that you fork the repository so you can push changes and submit pull requests.

2. Clone the forked Repository locally
    ```sh
    git clone https://github.com/YOUR-USERNAME/gifsync.git
    cd gifsync
    ```

2. (Optional) Create a Python virtual environment
    ```sh
    sudo apt update
    sudo apt install python3-venv
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install required modules
    ```sh
    python3 -m pip install -r requirements.txt
    ```

4. Run the server
    ```sh
    python3 -m run
    ```

### Making Changes
1. Create your Feature Branch (`git checkout -b feature/SomeFeature`)
2. Make some changes and stage them (`git add .`)
3. Commit your Changes (`git commit -m 'Add some Feature'`)
    - If you make multiple commits, please [squash them][squash-url] into a single commit before Pushing or opening a Pull request
4. Push to the Branch (`git push origin feature/SomeFeature`)
5. Open a Pull Request on GitHub
