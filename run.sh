#!/bin/sh

# Create an empty google.json file if it doesn't exist
if [ ! -f google.json ]; then
    echo "{}" > google.json
    echo "Created empty google.json file."
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    . venv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the vol.py script
echo "Running vol.py..."
python3 vol.py

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi

echo "Script execution completed."