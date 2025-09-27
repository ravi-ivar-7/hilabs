## Quick Setup

1. **Setup virtual environment and install dependencies:**
   ```bash
   ./setup-backend.sh
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```