# STEVE: Smart Tech-Enabled Virtual Entity

STEVE is an advanced AI assistant designed to be intelligent, adaptable, and user-friendly. This project uses Rasa for natural language processing, FastAPI for the backend, and React for the frontend.

## Prerequisites

- Python 3.9
- Node.js 14+
- npm 6+

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/STEVE.git
   cd STEVE
   ```

2. Run the setup script:
   ```
   setup.bat
   ```

   This script will:
   - Create and activate a virtual environment
   - Install all required Python packages
   - Train the Rasa model

3. Start the backend:
   ```
   cd backend
   uvicorn main:app --reload
   ```

4. In a new terminal, start the frontend:
   ```
   cd frontend
   npm install
   npm start
   ```

## Usage

After starting both the backend and frontend, you can interact with STEVE through the web interface at `http://localhost:3000`.

## Project Structure
