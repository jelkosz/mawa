# Standalone Execution Module

This Python module is designed to be executed in standalone mode. It supports both application launch and test execution workflows.

## 📦 Prerequisites

Make sure you're using [Poetry](https://python-poetry.org/) as your package manager.

## 🚀 Running the Application

To run the application:

```bash
cd src/mawa
poetry run adk web
```

This command starts the application in standalone mode using the ADK framework.

✅ Running Tests

To execute the end-to-end tests:

```bash
cd src/mawa
poetry run adk eval standalone standalone/end_to_end_tests.evalset.json
```

This command runs the standalone evaluation tests defined in the provided .json file.

🛠 Notes

All commands should be run from within the src/mawa directory.

Ensure your environment is set up with any required dependencies using Poetry before executing.