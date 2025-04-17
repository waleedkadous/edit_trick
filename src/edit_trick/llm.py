"""LLM interaction for the edit trick demonstration."""

import time
from typing import Dict, List, Tuple, Any

import anthropic
from anthropic.types import MessageParam


class LLMProcessor:
    """Handles interactions with the Anthropic Claude API."""

    def __init__(self, api_key: str):
        """
        Initialize the LLM processor.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-latest"

    def process_full_document(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process the entire document with the LLM to add headings.
        
        Args:
            text: The input document text
            
        Returns:
            Tuple of (modified text, metadata with token usage and time)
        """
        start_time = time.time()
        
        system_prompt = """
        You are an expert editor who adds helpful section headings to documents.
        Analyze the text and insert appropriate section headings where logical sections begin.
        The headings should be concise (3-6 words) and reflect the content that follows.
        Format each heading on its own line with markdown H2 style: ## Heading Text
        Do not modify the original text except to add these headings.
        """
        
        user_message = f"Please add appropriate section headings to this document:\n\n{text}"
        
        message_params: List[MessageParam] = [
            {
                "role": "user",
                "content": user_message,
            }
        ]
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=message_params,
            max_tokens=4000,
        )
        
        end_time = time.time()
        
        output_text = response.content[0].text
        
        metadata = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            "processing_time": end_time - start_time,
            "approach": "full_document"
        }
        
        return output_text, metadata

    def generate_edits(self, text: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """
        Generate a list of edits to add headings using the edit trick.
        
        Args:
            text: The input document text
            
        Returns:
            Tuple of (list of edits, metadata with token usage and time)
        """
        start_time = time.time()
        
        system_prompt = """
        You are an expert editor who identifies where section headings should be added to documents.
        Instead of modifying the document directly, you will identify logical sections and suggest
        appropriate headings for each.
        
        Your task is to analyze the document and output a series of edit operations in sed-like syntax.
        Each edit should be on its own line and have the format:
        
        s/unique text marker/## Heading Text\\n\\n$0/
        
        Where:
        - "unique text marker" is 40-60 characters of text that uniquely identifies the start of a section
        - "## Heading Text" is a concise (3-6 words) heading that reflects the section content
        - "\\n\\n$0" keeps the original text after adding the heading
        
        Important formatting rules:
        1. Escape any forward slashes (/) in the text with a backslash: \\/
        2. Put each edit on its own line
        3. Use "## " for all headings (markdown H2 style)
        4. Include NO explanation or commentary - ONLY the edit commands
        """
        
        user_message = f"Analyze this document and identify where headings should be added. Return only edit operations in sed-like syntax, one per line:\n\n{text}"
        
        message_params: List[MessageParam] = [
            {
                "role": "user",
                "content": user_message,
            }
        ]
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=message_params,
            max_tokens=4000,
        )
        
        end_time = time.time()
        
        # Extract the edit commands from the response
        output_text = response.content[0].text
        
        # Clean up any potential markdown code block formatting
        if "```" in output_text:
            # Extract content between code blocks if present
            if output_text.startswith("```") and "```" in output_text[3:]:
                output_text = output_text.split("```", 2)[1]
                if output_text.startswith("sed") or output_text.startswith("bash"):
                    output_text = output_text.split("\n", 1)[1]
            else:
                # Remove all code block markers
                output_text = output_text.replace("```", "")
        
        # Store raw commands for saving to file
        raw_commands = []
        
        # Parse the edit commands for internal use
        edits = []
        for line in output_text.strip().split('\n'):
            line = line.strip()
            if line and line.startswith('s/'):
                # Save the raw command
                raw_commands.append(line)
                
                try:
                    # Split by forward slash, but respect escaped slashes
                    parts = []
                    current = ""
                    escape = False
                    for char in line[2:]:  # Skip the 's/'
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
                    
                    if len(parts) >= 2:
                        section_start = parts[0].replace('\\/', '/')
                        heading = parts[1].split('\\n\\n')[0]
                        
                        edits.append({
                            "section_start": section_start,
                            "heading": heading,
                            "raw_command": line
                        })
                except Exception:
                    # Skip invalid edit commands
                    continue
        
        # Create the metadata
        metadata = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            "processing_time": end_time - start_time,
            "approach": "edit_trick",
            "edit_count": len(edits),
            "raw_commands": raw_commands
        }
        
        return edits, metadata


def apply_edits(text: str, edits: List[Dict[str, str]]) -> str:
    """
    Apply a list of edits to the original document text.
    
    Args:
        text: The original document text
        edits: List of edit operations from generate_edits
        
    Returns:
        The modified document text
    """
    modified_text = text
    
    # Sort edits by position in the text (earliest first)
    sorted_edits = sorted(
        [(edit, text.find(edit["section_start"])) for edit in edits if text.find(edit["section_start"]) != -1],
        key=lambda x: x[1]
    )
    
    # Apply edits from last to first to avoid changing positions
    for edit, position in reversed(sorted_edits):
        section_start = edit["section_start"]
        heading = edit["heading"] + "\n\n"
        
        modified_text = (
            modified_text[:position] + 
            heading + 
            modified_text[position:]
        )
    
    return modified_text