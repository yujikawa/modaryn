from rich.console import Console
from pathlib import Path

def display_logo():
    console = Console()
    
    # Dynamically find the project root from the current file's location
    # This assumes the structure: project_root/modaryn/outputs/logo.py
    current_file_path = Path(__file__)
    project_root = current_file_path.parent.parent.parent 
    
    logo_path = project_root / "modaryn" / "assets" / "logo.txt"
    
    if logo_path.exists():
        logo_content = logo_path.read_text()
        console.print(logo_content, style="bold cyan")
    else:
        # Fallback or error handling if logo.txt is not found
        console.print("[bold red]Error: Logo file not found.[/bold red]")
