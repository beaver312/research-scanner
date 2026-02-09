"""
Interactive Setup Wizard for Research Scanner
Helps users select a research domain and configure their scanner
"""

import sys
from pathlib import Path

# Add research_scanner to path
sys.path.insert(0, str(Path(__file__).parent / "research_scanner"))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from template_manager import TemplateManager
import yaml

console = Console()


def show_welcome():
    """Display welcome message"""
    welcome = """
[bold cyan]Research Scanner Setup Wizard[/bold cyan]

Welcome! This wizard will help you set up automated research paper scanning
for your specific field of study.

[bold]What this tool does:[/bold]
• Automatically scans research databases (arXiv, PubMed, HuggingFace)
• Filters papers by relevance to your topics
• Indexes papers for easy searching
• Provides review workflow for quality control

Let's get started!
    """.strip()
    
    console.print(Panel(welcome, border_style="cyan"))
    console.print()


def select_template(manager):
    """Let user select a research domain template"""
    templates = manager.list_templates()
    
    console.print("[bold]Available Research Domains:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Domain", style="white", width=35)
    table.add_column("Description", style="dim")
    
    for i, template in enumerate(templates, 1):
        table.add_row(
            str(i),
            template['domain'],
            template['description'][:60] + "..." if len(template['description']) > 60 else template['description']
        )
    
    console.print(table)
    console.print()
    
    choice = IntPrompt.ask(
        "Select a domain",
        choices=[str(i) for i in range(1, len(templates) + 1)]
    )
    
    selected = templates[int(choice) - 1]
    return selected['name']


def show_template_details(manager, template_name):
    """Show detailed info about selected template"""
    info = manager.get_template_info(template_name)
    template = manager.load_template(template_name)
    
    details = f"""
[bold cyan]{info['domain']}[/bold cyan]
[dim]{info['description']}[/dim]

[bold]Configuration:[/bold]
• Topics Monitored: {info['num_topics']}
• Enabled Sources: {', '.join(info['enabled_sources'])}
• Relevance Threshold: {info['relevance_threshold']}

[bold]Sample Topics:[/bold]
    """.strip()
    
    for topic in template.topics[:3]:
        details += f"\n  • {topic.name} (weight: {topic.weight})"
        details += f"\n    Keywords: {', '.join(topic.keywords[:5])}"
    
    if len(template.topics) > 3:
        details += f"\n  ... and {len(template.topics) - 3} more topics"
    
    console.print(Panel(details, border_style="blue"))
    console.print()


def customize_topics(template):
    """Allow user to add custom topics"""
    if not Confirm.ask("Would you like to add custom topics to track?", default=False):
        return template
    
    console.print("\n[bold]Add Custom Topics[/bold]")
    console.print("[dim]Press Enter with empty name when done[/dim]\n")
    
    while True:
        topic_name = Prompt.ask("Topic name (or press Enter to finish)", default="")
        if not topic_name:
            break
        
        keywords_str = Prompt.ask("Keywords (comma-separated)")
        keywords = [k.strip() for k in keywords_str.split(',')]
        
        weight = IntPrompt.ask("Importance weight (1-5)", default=3)
        weight = weight / 3.0  # Convert to 0.3-1.7 scale
        
        from template_manager import TopicConfig
        new_topic = TopicConfig(
            name=topic_name,
            keywords=keywords,
            weight=weight
        )
        
        template.topics.append(new_topic)
        console.print(f"[green]✓ Added topic: {topic_name}[/green]\n")
    
    return template


def configure_settings(template):
    """Configure scanner settings"""
    console.print("\n[bold]Scanner Settings[/bold]\n")
    
    if Confirm.ask(
        f"Use default relevance threshold ({template.relevance_threshold})?",
        default=True
    ):
        pass
    else:
        template.relevance_threshold = IntPrompt.ask(
            "Relevance threshold (0-100%)",
            default=int(template.relevance_threshold * 100)
        ) / 100.0
    
    if Confirm.ask(
        f"Use default lookback period ({template.days_lookback} days)?",
        default=True
    ):
        pass
    else:
        template.days_lookback = IntPrompt.ask(
            "Days to look back when scanning",
            default=template.days_lookback
        )
    
    return template


def save_configuration(manager, template_name, template):
    """Save configuration to user config file"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "user_config.yaml"
    
    # Save template
    manager.save_template("user_config", template)
    
    # Also create a reference to the base template
    metadata = {
        'base_template': template_name,
        'configured_at': str(Path(__file__).parent),
        'domain': template.domain
    }
    
    with open(config_dir / "metadata.yaml", 'w') as f:
        yaml.dump(metadata, f)
    
    return config_path


def show_next_steps(config_path):
    """Show what to do next"""
    next_steps = f"""
[bold green]Setup Complete![/bold green]

Your configuration has been saved to:
[cyan]{config_path}[/cyan]

[bold]Next Steps:[/bold]

1. [bold]Start the API server:[/bold]
   cd D:\\Claude\\Projects\\scholars-terminal
   python Scholars_api.py

2. [bold]Run your first scan:[/bold]
   curl -X POST http://localhost:8000/api/research/scan

3. [bold]Review papers:[/bold]
   python review_papers.py interactive

4. [bold]Check results:[/bold]
   curl http://localhost:8000/api/research/latest

[dim]Tip: Papers will be added to staging for review before permanent storage.
Use the review workflow to curate your database![/dim]
    """.strip()
    
    console.print(Panel(next_steps, border_style="green"))


@click.command()
def setup():
    """Run the interactive setup wizard"""
    try:
        manager = TemplateManager()
        
        # Welcome
        show_welcome()
        
        # Select template
        console.print("[bold cyan]Step 1: Choose Your Research Domain[/bold cyan]\n")
        template_name = select_template(manager)
        console.print()
        
        # Show details
        console.print("[bold cyan]Step 2: Review Configuration[/bold cyan]\n")
        show_template_details(manager, template_name)
        
        if not Confirm.ask("Use this template?", default=True):
            console.print("[yellow]Setup cancelled[/yellow]")
            return
        
        # Load template
        template = manager.load_template(template_name)
        
        # Customize
        console.print("\n[bold cyan]Step 3: Customize (Optional)[/bold cyan]\n")
        template = customize_topics(template)
        template = configure_settings(template)
        
        # Save
        console.print("\n[bold cyan]Step 4: Save Configuration[/bold cyan]\n")
        config_path = save_configuration(manager, template_name, template)
        console.print(f"[green]✓ Configuration saved to {config_path}[/green]\n")
        
        # Next steps
        show_next_steps(config_path)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    setup()
