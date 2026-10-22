# WIT Library Chatbot (Ollama Edition)

This project is an upgraded local prototype for the Western Institute of Technology (WIT) Library Chatbot, powered by local Ollama (`llama3:latest`) and an intelligent backend topic-validation filter.

## Features

- **Strict Library-Only Filter**: Evaluates and accepts library questions across 10 distinct categories while immediately rejecting out-of-scope questions (mathematics, programming, general trivia, weather, food ordering, etc.) with the exact required refusal message.
- **Ollama API Integration**: Connects via `http://localhost:11434/api/chat` using `llama3:latest` without exposing sensitive configuration to the frontend.
- **Verified Knowledge Base**: Enforces verified WIT Library policies regarding operating hours, borrowing limits, overdue fines, library card registration, and clarifies that catalog queries require campus OPAC terminals.
- **Preserved Orange-and-White UI**: Retains the authentic WIT Library visual identity, greeting, suggested buttons, messenger typing indicator, and conversation context.
- **Zero External Dependencies**: Operates entirely using Python standard libraries.

## Configuration (.env)

The application reads configuration from environment variables or a local `.env` file:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
```

## How to Run on Windows

1. Ensure Ollama is running and has `llama3:latest` installed:
   ```powershell
   ollama serve
   ollama pull llama3:latest
   ```

2. Start the web application:
   ```powershell
   python app.py
   ```

3. Open your browser and navigate to:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Running Tests

- **Run Standard Evaluation Queries**:
  ```powershell
  python run_tests.py
  ```
  Generates reproducible results in `test_results.json` (100% accuracy on standard test set).

- **Run 10-Point Comprehensive Test Suite**:
  ```powershell
  python test_suite.py
  ```
  Validates general book queries, verified hours, borrowing rules, catalog availability verification, APA citation support, exact refusal message on unrelated queries, ambiguous query clarification, mixed query handling, offline Ollama graceful fallback, and UI elements.

## Project Files

- `app.py`: Web server, frontend HTML/CSS/JS, request routing, and response coordinator.
- `config.py`: Environment variable configuration and settings.
- `library_data.py`: Verified WIT Library information across all 10 supported categories.
- `topic_validator.py`: Backend pre-validation engine enforcing strict library-only responses.
- `ollama_client.py`: Ollama `/api/chat` client with error handling and system prompt integration.
- `test_suite.py`: Comprehensive test runner covering all required acceptance cases.
- `run_tests.py`: Evaluation script matching `test_queries.csv`.
- `test_results.json`: Execution log and accuracy metrics from test queries.
