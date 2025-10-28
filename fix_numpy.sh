#!/bin/bash
# Fix NumPy compatibility issue

echo "Fixing NumPy compatibility..."

# First, check if virtual environment is active
if [ -n "$VIRTUAL_ENV" ] || [ -d ".trading" ]; then
    echo "Virtual environment detected"
    
    # Reinstall numpy with compatible version
    pip install --upgrade "numpy<2"
    
    echo "✓ NumPy fixed"
else
    echo "No virtual environment detected, installing globally..."
    pip3 install --upgrade "numpy<2"
    echo "✓ NumPy fixed"
fi

echo ""
echo "Now test with: python3 test_runner.py"



