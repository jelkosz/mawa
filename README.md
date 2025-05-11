# Multi-Agent Web App (mawa)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Google ADK](https://img.shields.io/badge/Google-ADK-orange)
![Gemini API](https://img.shields.io/badge/Google-Gemini%20API-green)
![Uvicorn](https://img.shields.io/badge/Web%20Server-Uvicorn-lightgrey)

## Project Overview

`mawa` (Multi-Agent Web App) is an experimental project designed to demonstrate and teach how to build a simple web application using the Google Agent Development Kit (ADK). This repository serves primarily as an educational resource, offering a hands-on approach to understanding agent-based systems and their integration into web environments with Google's tools.

While not intended for production use, `mawa` provides a practical learning environment. Learning new concepts by applying them to familiar problems is a powerful method, and this project aims to facilitate that process for those interested in the Google ADK and multi-agent architectures.

## Getting Started

To run `mawa` locally, follow the instructions below.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.9+**: This project uses modern Python features.
* **Poetry**: A dependency management and packaging tool for Python. If you don't have it, you can install it by following the instructions on the [Poetry website](https://python-poetry.org/docs/#installation).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/mawa.git](https://github.com/your-username/mawa.git)
    cd mawa
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

### Configuration

To enable the application to interact with the Google Gemini API, you need to set up your API key:

1.  Navigate to the `src/mawa` directory:
    ```bash
    cd src/mawa
    ```

2.  Create a new file named `.env` in this directory.

3.  Add the following content to the `.env` file, replacing `<your gemini API key>` with your actual Google Gemini API key:

    ```env
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY=<your gemini API key>
    ```

    **Note:** You can obtain a Google Gemini API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).

### Running the Application

You have two primary methods to run the `mawa` application: using the ADK web server or directly via PyCharm.

#### 1. Running with ADK Web

This method utilizes the Google ADK's built-in web server capabilities.

1.  Ensure you are in the `src` directory:
    ```bash
    cd src
    ```
    (If you are still in `src/mawa`, navigate back one level: `cd ..`)

2.  Execute the following command to start the ADK web server:
    ```bash
    poetry run adk web
    ```

    The application should now be accessible in your web browser, typically at `http://localhost:8000`.

#### 2. Running in PyCharm

For developers using PyCharm, you can configure a run configuration to launch the application.

1.  **Open your project in PyCharm.**

2.  **Create a new Python Run/Debug Configuration:**
    * Go to `Run` -> `Edit Configurations...`
    * Click the `+` icon and select `Python`.

3.  **Configure the settings:**
    * **Module name:** Select `uvicorn`
    * **Parameters:** Set to `mawa.main:app --reload --app-dir src`
    * **Environment variables:** Add `GOOGLE_API_KEY=<your gemini API key>` (replace with your actual key). You can click the folder icon to easily add this variable.

4.  **Apply** the changes and **Run** the configuration.

---

## Disclaimer

This project is purely for educational purposes and to demonstrate concepts related to the Google Agent Development Kit. It is not designed for production environments and may not follow best practices for security, scalability, or robustness required for such use cases. Use it as a learning tool to explore the capabilities of ADK and multi-agent web applications.
