# Edit Trick

This project demonstrates the "edit trick" - a more efficient approach to using LLMs for document modification tasks that reduces token usage, processing time, and handles longer documents.

## The Problem

When using LLMs to modify or annotate documents (adding headlines, inserting footnotes or links etc), the obvious approach is to pass the entire document to the LLM and have it return the modified version. This works but is inefficient in terms of:

- Token usage (cost)
- Processing time
- Context window limitations

## The Solution: The Edit Trick

Instead of processing the entire document, the "edit trick" involves:

1. Having the LLM generate a list of specific edits to apply
2. Applying those edits to the original document

This approach is:
- Faster ⚡
- Cheaper 💰
- Works with longer documents 📄
- Maintains quality ✅

## Installation

```bash
# Clone the repository
git clone https://github.com/waleedkadous/edit-trick.git
cd edit-trick

# Create and activate a virtual environment using uv
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e .
```

## Usage

The tool provides two approaches for adding headings to a document:

```bash
# Traditional approach - pass entire document to LLM
edit-trick full input.txt output.txt

# Edit trick approach - generate and apply edits
edit-trick edit input.txt output.txt

# Save the edits to a JSON file
edit-trick edit input.txt output.txt --save-edits edits.json

# Apply pre-generated edits
edit-trick apply-edits input.txt edits.json output.txt

# Benchmark both approaches
edit-trick benchmark input.txt --output-dir results/
```

### API Key

You'll need an Anthropic API key. Set it as an environment variable:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```