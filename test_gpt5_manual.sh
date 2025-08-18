#!/bin/bash

# Test script for GPT-5 fix
echo "Testing GPT-5 fix..."

# Activate virtual environment
source open_interpreter_env/bin/activate

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Please set your OPENAI_API_KEY:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

echo "API key is set. Testing interpreter with GPT-5..."

# Test with a simple command
echo 'print("Hello from GPT-5!")' | interpreter -y --model gpt-5

echo "If you see the Python output above and no max_tokens error, the fix is working! 🎉"
