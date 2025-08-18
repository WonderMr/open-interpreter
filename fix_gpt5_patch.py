#!/usr/bin/env python3
"""
Patch for Open Interpreter to fix GPT-5 max_tokens/max_completion_tokens issue.
This script patches the LLM module to use max_completion_tokens for models that require it.
"""

import os
import shutil
import sys

def needs_max_completion_tokens(model_name):
    """
    Check if a model needs max_completion_tokens instead of max_tokens.
    
    Args:
        model_name (str): The model name
        
    Returns:
        bool: True if the model needs max_completion_tokens
    """
    # List of models that require max_completion_tokens
    models_needing_max_completion_tokens = [
        'gpt-5',
        'o1-preview',
        'o1-mini',
        'o3-mini'
    ]
    
    # Check if the model name (without provider prefix) is in the list
    model_base = model_name.split('/')[-1].lower()
    return any(model_base.startswith(model.lower()) for model in models_needing_max_completion_tokens)

def apply_patch():
    """Apply the patch to fix the max_tokens/max_completion_tokens issue."""
    
    # Find the interpreter installation
    import interpreter
    interpreter_path = os.path.dirname(interpreter.__file__)
    llm_file = os.path.join(interpreter_path, 'core', 'llm', 'llm.py')
    
    if not os.path.exists(llm_file):
        print(f"Error: Could not find {llm_file}")
        return False
    
    print(f"Patching {llm_file}...")
    
    # Create backup
    backup_file = llm_file + '.backup'
    if not os.path.exists(backup_file):
        shutil.copy2(llm_file, backup_file)
        print(f"Created backup: {backup_file}")
    
    # Read the original file
    with open(llm_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already patched
    if 'max_completion_tokens' in content and 'needs_max_completion_tokens' in content:
        print("File appears to already be patched.")
        return True
    
    # Define the patch
    patch_function = '''
def needs_max_completion_tokens(model_name):
    """
    Check if a model needs max_completion_tokens instead of max_tokens.
    
    Args:
        model_name (str): The model name
        
    Returns:
        bool: True if the model needs max_completion_tokens
    """
    # List of models that require max_completion_tokens
    models_needing_max_completion_tokens = [
        'gpt-5',
        'o1-preview', 
        'o1-mini',
        'o3-mini'
    ]
    
    # Check if the model name (without provider prefix) is in the list
    model_base = model_name.split('/')[-1].lower()
    return any(model_base.startswith(model.lower()) for model in models_needing_max_completion_tokens)

'''
    
    # Find the line where max_tokens is set in params
    lines = content.split('\n')
    patched_lines = []
    
    for i, line in enumerate(lines):
        if 'params["max_tokens"] = self.max_tokens' in line:
            # Replace the line with conditional logic
            indent = line[:len(line) - len(line.lstrip())]  # Get indentation
            patched_lines.append(f'{indent}if needs_max_completion_tokens(model):')
            patched_lines.append(f'{indent}    params["max_completion_tokens"] = self.max_tokens')
            patched_lines.append(f'{indent}else:')
            patched_lines.append(f'{indent}    params["max_tokens"] = self.max_tokens')
        else:
            patched_lines.append(line)
    
    # Add the function at the top of the file (after imports)
    final_lines = []
    added_function = False
    
    for line in patched_lines:
        final_lines.append(line)
        # Add function after the last import but before the first class
        if not added_function and line.startswith('class ') and 'Llm' in line:
            # Insert the function before the class
            final_lines.insert(-1, patch_function)
            added_function = True
    
    # Write the patched file
    patched_content = '\n'.join(final_lines)
    
    with open(llm_file, 'w', encoding='utf-8') as f:
        f.write(patched_content)
    
    print("✓ Patch applied successfully!")
    print("The fix will detect models that need max_completion_tokens and use the correct parameter.")
    return True

def restore_backup():
    """Restore the original file from backup."""
    import interpreter
    interpreter_path = os.path.dirname(interpreter.__file__)
    llm_file = os.path.join(interpreter_path, 'core', 'llm', 'llm.py')
    backup_file = llm_file + '.backup'
    
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, llm_file)
        print(f"✓ Restored original file from {backup_file}")
        return True
    else:
        print("No backup file found.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_backup()
    else:
        apply_patch()