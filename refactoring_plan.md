# Refactoring Plan for `app_api/api.py`

The goal is to split the monolithic `app_api/api.py` (900+ lines) into smaller, manageable modules using Flask Blueprints. This will improve maintainability and readability.

## 1. Proposed Directory Structure

We will create a `routes` package and a `services` package to organize the code.

```text
app_api/
├── __init__.py          # Exports create_app
├── api.py               # Main entry point (initializes app, registers blueprints)
├── config.py            # Configuration (Existing)
├── services/            # Shared logic and services
│   ├── __init__.py
│   ├── agent_service.py # Manages KMAgent instances (get_or_create_km_agent)
│   └── validators.py    # Validation helpers (allowed_file, allowed_image)
└── routes/              # Route definitions (Blueprints)
    ├── __init__.py
    ├── chat.py          # /api/chat
    ├── documents.py     # /api/documents, /api/upload
    ├── instructions.py  # /api/instructions
    ├── images.py        # /api/analyze-image
    └── health.py        # /health
```

## 2. Module Responsibilities

### `services/agent_service.py`
- **Responsibility**: Manage `KMAgent` instances and the `vectorizer`.
- **Content**:
    - `km_agent_cache` (Global dictionary)
    - `get_or_create_km_agent(owner)`
    - `init_services()` (Initialize vectorizer)
    - `get_vectorizer()` (Access global vectorizer)

### `services/validators.py`
- **Responsibility**: File validation.
- **Content**:
    - `allowed_file(filename)`
    - `allowed_image(filename)`

### `routes/*.py` (Blueprints)
Each file will define a Flask Blueprint.
- **`chat.py`**: Handles chat interactions and SSE streaming.
- **`documents.py`**: Handles document listing, uploading (with progress), deletion, and visibility updates.
- **`instructions.py`**: CRUD operations for user instructions.
- **`images.py`**: Image analysis endpoint.
- **`health.py`**: Health check endpoint.

### `api.py` (Main Application Factory)
- **Responsibility**: Create Flask app, configure it, and register blueprints.
- **Content**:
    - `create_app()` function.
    - Blueprint registration.
    - Global error handlers (if any).

## 3. Implementation Steps

1.  **Create Directories**: Create `app_api/routes` and `app_api/services`.
2.  **Extract Services**:
    - Move `allowed_file`, `allowed_image` to `services/validators.py`.
    - Move `get_or_create_km_agent` and `init_services` to `services/agent_service.py`.
3.  **Create Blueprints**:
    - Create `routes/chat.py` and move `chat` route logic there.
    - Create `routes/documents.py` and move `get_documents`, `upload_pdf`, `delete_document`, etc.
    - Create `routes/instructions.py` and move instruction routes.
    - Create `routes/images.py` and move `analyze_image`.
    - Create `routes/health.py` and move `health_check`.
4.  **Update `api.py`**:
    - Import blueprints.
    - Remove old route functions.
    - Register blueprints using `app.register_blueprint()`.
5.  **Verify**: Ensure all endpoints work as expected.

## 4. Code Example (Blueprint Pattern)

**`app_api/routes/chat.py`**:
```python
from flask import Blueprint, request, Response, stream_with_context
from app_api.services.agent_service import get_or_create_km_agent
from ks_infrastructure import get_current_user

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    # ... logic moved from api.py ...
    pass
```

**`app_api/api.py`**:
```python
from flask import Flask
from app_api import config
from app_api.routes.chat import chat_bp
from app_api.routes.documents import documents_bp
# ... other imports

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(documents_bp)
    # ...

    return app
```
