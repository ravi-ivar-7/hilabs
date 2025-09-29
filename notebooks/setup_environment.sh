#!/bin/bash

echo "Setting up CPU-only virtual environment for HiLabs notebooks..."

source venv/bin/activate

pip install --upgrade pip

# Install CPU-only requirements (much smaller downloads)
pip install -r requirements_cpu.txt

# Download spaCy model
python -m spacy download en_core_web_sm

echo "CPU-only virtual environment setup complete!"
echo "To activate: source venv/bin/activate"
echo "To run: python HiLabs_Clause_Classifier_Fixed.py"
echo ""
echo "Note: This version uses CPU-only PyTorch (~100MB vs 887MB)"
