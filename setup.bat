@echo off

echo Checking Python version...
py -3.9 --version

if %errorlevel% neq 0 (
    echo Python 3.9 is not installed or not in PATH. Please install Python 3.9 and try again.
    exit /b %errorlevel%
)

echo Creating virtual environment...
py -3.9 -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel

echo Installing requirements...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Error occurred while installing requirements.
    echo Please check your Python version and ensure it's compatible with the required packages.
    exit /b %errorlevel%
)

echo Setting up Rasa...
cd backend\rasa_model
rasa train

echo Setup complete!
