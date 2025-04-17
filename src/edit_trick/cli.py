"""Command-line interface for the edit trick demonstration."""

import json
import os
import time
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from edit_trick.apply import apply_sed_edits, load_edit_commands
from edit_trick.llm import LLMProcessor, apply_edits

# Load environment variables from .env file
load_dotenv()

console = Console()
app = typer.Typer(help="Demonstration of the edit trick for LLM document processing")


def get_api_key() -> str:
    """Get the Anthropic API key from .env file or environment variables."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            Panel(
                "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found.\n\n"
                "Please add it to a .env file in the project directory:\n"
                "ANTHROPIC_API_KEY=your_key_here\n\n"
                "Or set it as an environment variable:\n"
                "export ANTHROPIC_API_KEY=your_key_here",
                title="API Key Required",
            )
        )
        raise typer.Exit(1)
        
    return api_key


@app.command("full")
def process_full_document(
    input_file: Path = typer.Argument(..., help="Path to the input document"),
    output_file: Path = typer.Argument(..., help="Path to save the output document"),
):
    """Process the document using the traditional full-document approach."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading input file:[/bold red] {e}")
        raise typer.Exit(1)

    api_key = get_api_key()
    processor = LLMProcessor(api_key)

    with console.status("[bold green]Processing document with full approach..."):
        output_text, metadata = processor.process_full_document(text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    # Display results
    console.print(
        Panel(
            f"[bold green]Document processed successfully![/bold green]\n"
            f"Input tokens: {metadata['input_tokens']}\n"
            f"Output tokens: {metadata['output_tokens']}\n"
            f"Total tokens: {metadata['total_tokens']}\n"
            f"Processing time: {metadata['processing_time']:.2f} seconds",
            title="Full Document Approach",
        )
    )


@app.command("edit")
def process_with_edit_trick(
    input_file: Path = typer.Argument(..., help="Path to the input document"),
    output_file: Path = typer.Argument(..., help="Path to save the output document"),
    save_edits: Optional[Path] = typer.Option(
        None, help="Path to save the generated edit commands"
    ),
):
    """Process the document using the edit trick approach."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading input file:[/bold red] {e}")
        raise typer.Exit(1)

    api_key = get_api_key()
    processor = LLMProcessor(api_key)

    with console.status("[bold green]Generating edits..."):
        edits, metadata = processor.generate_edits(text)

    with console.status("[bold green]Applying edits..."):
        start_time = time.time()
        output_text = apply_edits(text, edits)
        apply_time = time.time() - start_time

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    if save_edits:
        with open(save_edits, "w", encoding="utf-8") as f:
            # Save raw edit commands
            for cmd in metadata["raw_commands"]:
                f.write(f"{cmd}\n")

    # Display results
    console.print(
        Panel(
            f"[bold green]Document processed successfully![/bold green]\n"
            f"Input tokens: {metadata['input_tokens']}\n"
            f"Output tokens: {metadata['output_tokens']}\n"
            f"Total tokens: {metadata['total_tokens']}\n"
            f"Generated edits: {len(edits)}\n"
            f"LLM processing time: {metadata['processing_time']:.2f} seconds\n"
            f"Edit application time: {apply_time:.2f} seconds\n"
            f"Total time: {metadata['processing_time'] + apply_time:.2f} seconds",
            title="Edit Trick Approach",
        )
    )


@app.command("apply-edits")
def apply_saved_edits(
    input_file: Path = typer.Argument(..., help="Path to the input document"),
    edits_file: Path = typer.Argument(..., help="Path to the file with edit commands"),
    output_file: Path = typer.Argument(..., help="Path to save the output document"),
):
    """Apply pre-generated edits to a document."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading input file:[/bold red] {e}")
        raise typer.Exit(1)

    try:
        # Try to detect format based on file extension
        if edits_file.suffix.lower() in ['.json', '.js']:
            # JSON format (old style)
            with open(edits_file, "r", encoding="utf-8") as f:
                edits = json.load(f)
            edit_count = len(edits)
            with console.status("[bold green]Applying JSON edits..."):
                start_time = time.time()
                output_text = apply_edits(text, edits)
                apply_time = time.time() - start_time
        else:
            # Sed-like format (new style)
            edit_commands = load_edit_commands(str(edits_file))
            edit_count = len(edit_commands)
            with console.status("[bold green]Applying sed-like edits..."):
                start_time = time.time()
                output_text = apply_sed_edits(text, edit_commands)
                apply_time = time.time() - start_time
    except Exception as e:
        console.print(f"[bold red]Error applying edits:[/bold red] {e}")
        raise typer.Exit(1)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)

    # Display results
    console.print(
        Panel(
            f"[bold green]Edits applied successfully![/bold green]\n"
            f"Applied {edit_count} edits\n"
            f"Processing time: {apply_time:.2f} seconds",
            title="Apply Edits",
        )
    )


@app.command("benchmark")
def benchmark(
    input_file: Path = typer.Argument(..., help="Path to the input document"),
    output_dir: Path = typer.Option(
        Path("./benchmark_results"), help="Directory to save benchmark results"
    ),
    runs: int = typer.Option(3, help="Number of benchmark runs to perform"),
):
    """Benchmark both approaches on the same document."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading input file:[/bold red] {e}")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = get_api_key()
    processor = LLMProcessor(api_key)

    full_results = []
    edit_results = []
    full_heading_counts = []
    edit_heading_counts = []

    for i in range(1, runs + 1):
        console.print(f"Run {i}/{runs}")

        # Full document approach
        with console.status(f"[bold green]Run {i}/{runs}: Processing with full approach..."):
            output_text, metadata = processor.process_full_document(text)
            # Count headings in output text (## format)
            heading_count = output_text.count("\n## ")
            if heading_count == 0:  # Try with single # too
                heading_count = output_text.count("\n# ")
            full_heading_counts.append(heading_count)
            metadata["heading_count"] = heading_count
            full_results.append(metadata)

        full_output_file = output_dir / f"full_output_{i}.txt"
        with open(full_output_file, "w", encoding="utf-8") as f:
            f.write(output_text)

        # Edit trick approach
        with console.status(f"[bold green]Run {i}/{runs}: Processing with edit trick..."):
            edits, metadata = processor.generate_edits(text)
            start_time = time.time()
            output_text = apply_edits(text, edits)
            apply_time = time.time() - start_time
            metadata["apply_time"] = apply_time
            metadata["total_time"] = metadata["processing_time"] + apply_time
            metadata["heading_count"] = len(edits)
            edit_heading_counts.append(len(edits))
            edit_results.append(metadata)

        edit_output_file = output_dir / f"edit_output_{i}.txt"
        with open(edit_output_file, "w", encoding="utf-8") as f:
            f.write(output_text)

        # Save raw edit commands
        edits_file = output_dir / f"edits_{i}.txt"
        with open(edits_file, "w", encoding="utf-8") as f:
            for cmd in metadata["raw_commands"]:
                f.write(f"{cmd}\n")

    # Save benchmark results
    benchmark_results = {
        "document_size": len(text),
        "full_results": full_results,
        "edit_results": edit_results,
    }

    with open(output_dir / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)

    # Calculate averages
    avg_full_input_tokens = sum(r["input_tokens"] for r in full_results) / len(full_results)
    avg_full_output_tokens = sum(r["output_tokens"] for r in full_results) / len(full_results)
    avg_full_time = sum(r["processing_time"] for r in full_results) / len(full_results)
    avg_full_headings = sum(full_heading_counts) / len(full_heading_counts)
    
    avg_edit_input_tokens = sum(r["input_tokens"] for r in edit_results) / len(edit_results)
    avg_edit_output_tokens = sum(r["output_tokens"] for r in edit_results) / len(edit_results)
    avg_edit_total_time = sum(r["total_time"] for r in edit_results) / len(edit_results)
    avg_edit_headings = sum(edit_heading_counts) / len(edit_heading_counts)

    # Pricing constants (per million tokens)
    INPUT_TOKEN_PRICE = 3.0  # $3 per million input tokens
    OUTPUT_TOKEN_PRICE = 15.0  # $15 per million output tokens
    
    # Calculate costs
    full_input_cost = avg_full_input_tokens * (INPUT_TOKEN_PRICE / 1000000)
    full_output_cost = avg_full_output_tokens * (OUTPUT_TOKEN_PRICE / 1000000)
    full_total_cost = full_input_cost + full_output_cost
    
    edit_input_cost = avg_edit_input_tokens * (INPUT_TOKEN_PRICE / 1000000)
    edit_output_cost = avg_edit_output_tokens * (OUTPUT_TOKEN_PRICE / 1000000)
    edit_total_cost = edit_input_cost + edit_output_cost
    
    cost_diff = full_total_cost - edit_total_cost
    cost_pct = (cost_diff / full_total_cost) * 100 if full_total_cost > 0 else 0
    
    # Display results in a table
    table = Table(title="Benchmark Results (Average)")
    table.add_column("Metric", style="cyan")
    table.add_column("Full Approach", style="green")
    table.add_column("Edit Trick", style="blue")
    table.add_column("Difference", style="yellow")

    # Compare costs (most important for efficiency)
    table.add_row(
        "Estimated Cost", 
        f"${full_total_cost:.6f}", 
        f"${edit_total_cost:.6f}",
        f"${cost_diff:.6f} ({cost_pct:.1f}%)"
    )
    
    # Compare output tokens
    output_token_diff = avg_full_output_tokens - avg_edit_output_tokens
    output_token_pct = (output_token_diff / avg_full_output_tokens) * 100 if avg_full_output_tokens > 0 else 0
    table.add_row(
        "Output Tokens", 
        f"{avg_full_output_tokens:.0f}", 
        f"{avg_edit_output_tokens:.0f}",
        f"{output_token_diff:.0f} ({output_token_pct:.1f}%)"
    )
    
    # Show input tokens
    input_token_diff = avg_full_input_tokens - avg_edit_input_tokens
    input_token_pct = (input_token_diff / avg_full_input_tokens) * 100 if avg_full_input_tokens > 0 else 0
    table.add_row(
        "Input Tokens", 
        f"{avg_full_input_tokens:.0f}", 
        f"{avg_edit_input_tokens:.0f}",
        f"{input_token_diff:.0f} ({input_token_pct:.1f}%)"
    )

    time_diff = avg_full_time - avg_edit_total_time
    time_pct = (time_diff / avg_full_time) * 100 if avg_full_time > 0 else 0
    table.add_row(
        "Processing Time", 
        f"{avg_full_time:.2f}s", 
        f"{avg_edit_total_time:.2f}s",
        f"{time_diff:.2f}s ({time_pct:.1f}%)"
    )

    heading_diff = avg_full_headings - avg_edit_headings
    table.add_row(
        "Headings Added", 
        f"{avg_full_headings:.0f}", 
        f"{avg_edit_headings:.0f}",
        f"{heading_diff:.0f}"
    )

    console.print(table)

    # Display summary
    console.print(
        Panel(
            f"[bold green]Benchmark completed![/bold green]\n"
            f"Results saved to: [bold]{output_dir}[/bold]\n\n"
            f"The edit trick approach was [bold]{'more expensive' if cost_pct < 0 else 'cheaper'}[/bold] "
            f"({'+' if cost_pct < 0 else '-'}{abs(cost_pct):.1f}%), "
            f"used [bold]{'more' if output_token_pct < 0 else 'fewer'}[/bold] output tokens "
            f"({'+' if output_token_pct < 0 else '-'}{abs(output_token_pct):.1f}%), and was "
            f"[bold]{'slower' if time_pct < 0 else 'faster'}[/bold] "
            f"({'+' if time_pct < 0 else '-'}{abs(time_pct):.1f}%)",
            title="Summary",
        )
    )


if __name__ == "__main__":
    app()