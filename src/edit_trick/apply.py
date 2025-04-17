"""Functions for applying edit commands to text."""

import re
from typing import List


def apply_sed_edits(text: str, edit_commands: List[str]) -> str:
    """
    Apply a list of sed-like edit commands to text.
    
    Args:
        text: The original text to modify
        edit_commands: List of sed-like edit commands (s/pattern/replacement/)
        
    Returns:
        The modified text
    """
    result = text
    
    for cmd in edit_commands:
        if not cmd.startswith('s/'):
            continue
            
        # Parse the command - split by '/' but respect escaped slashes
        parts = []
        current = ""
        escape = False
        
        for char in cmd[2:]:  # Skip the 's/'
            if escape:
                current += char
                escape = False
            elif char == '\\':
                escape = True
            elif char == '/' and not escape:
                parts.append(current)
                current = ""
            else:
                current += char
                
        if len(parts) < 2:
            continue
            
        pattern = parts[0].replace('\\/', '/')
        replacement = parts[1].replace('\\n', '\n').replace('$0', pattern)
        
        # Escape special regex characters but keep the pattern as a literal string
        pattern_escaped = re.escape(pattern)
        
        # Apply the substitution - replace the first occurrence only
        result = re.sub(pattern_escaped, replacement, result, count=1)
    
    return result


def load_edit_commands(file_path: str) -> List[str]:
    """
    Load edit commands from a file.
    
    Args:
        file_path: Path to the file containing edit commands
        
    Returns:
        List of edit commands
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        commands = [line.strip() for line in f if line.strip().startswith('s/')]
    
    return commands