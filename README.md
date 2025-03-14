# Lyric Learn

Japanese Lyric Learner is a Python application designed to analyze Japanese song lyrics. It uses the OpenAI API to provide detailed translations and explanations of the lyrics.

## Features

- Analyzes Japanese song lyrics in batches.
- Provides accurate translations and detailed explanations of grammar and key vocabulary.
- Saves the analysis results to output files.

## Requirements

- Python 3.11.11
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd japanese-lyric-learner
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
3. Create a `.env` file in the root directory and add your OpenAI API key, model name, and base URL:
    ```env
    OPENAI_API_KEY=your_openai_api_key
    MODEL_NAME=qwen-plus
    BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    ```

4. If you want to use the OpenAI GPT model, update your `.env` file as follows:
    ```env
    OPENAI_API_KEY=your_openai_api_key
    MODEL_NAME=gpt-4o  # Default is gpt-3.5-turbo
    BASE_URL=https://api.openai.com/v1  # Default OpenAI API URL
    ```
## Usage

1. Place your song lyrics in the `original_song/learned` or `original_song/to_learn` directories.

2. Run the main script:
    ```sh
    python main.py
    ```

3. The analysis results will be saved in the `output/learned` or `output/to_learn` directories.

4. Run the main script to generate a test analysis file for reference:
    ```sh
    python main.py
    ```

    This will create a file named `test_analyze.txt` in the `output` directory, which you can use as a reference for the analysis results.

## License

This project is licensed under the MIT License.