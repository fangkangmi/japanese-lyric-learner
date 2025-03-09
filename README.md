# Lyric Learn

Lyric Learn is a Python application designed to help users learn song lyrics. This README provides an overview of the project, how to set it up, and how to use it.

## Features

- Display song lyrics
- Interactive learning mode
- Progress tracking

## Requirements

- Python 3.11.11
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/lyric_learn.git
    ```
2. Navigate to the project directory:
    ```bash
    cd lyric_learn
    ```
3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1. Set up your API key in the environment variables:
    ```bash
    export API_KEY=your_api_key_here
    2. If you want to use a different model, modify the `client` initialization in `main.py`:
        ```python
        client = OpenAI(
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
        ```

    ### Example Configurations

    - **Using OpenAI**: No need to edit the base URL.
        ```python
        client = OpenAI()
        ```

    - **Using Another Model (e.g., DashScope)**:
        ```python
        client = OpenAI(
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
        ```


## Usage

Run the main script to start the application:
```bash
python main.py
```

## Project Structure

- `main.py`: The main script to run the application.
- `requirements.txt`: List of required Python packages.
- `README.md`: Project documentation.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
