import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent import ApplicationAgent
from tools.data_tools import (
    add_application,
    get_applications,
    get_application_stats,
    list_cover_letters
)

app = typer.Typer()
console = Console()


@app.command()
def apply(
    company: str = typer.Option(None, "--company", "-c", help="Company name"),
    role: str = typer.Option(None, "--role", "-r", help="Job title"),
    job_url: str = typer.Option(None, "--url", "-u", help="Job posting URL"),
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider: groq, google, openai"),
):
    """
    Generate a tailored cover letter and track the application.

    This command will:
    1. Ask for job details (company, role, description)
    2. Generate a tailored cover letter using AI
    3. Save the application to the database
    4. Optionally save the cover letter file
    """
    console.print("\n[bold cyan]🤖 AI Application Assistant[/bold cyan]\n")

    # Get company if not provided
    if not company:
        company = Prompt.ask("[bold]Company name[/bold]")

    # Get role if not provided
    if not role:
        role = Prompt.ask("[bold]Job title/role[/bold]")

    # Get job URL if not provided
    if not job_url:
        job_url = Prompt.ask("[bold]Job posting URL[/bold] (optional)", default="")

    # Get job description
    console.print("\n[bold]Paste the job description below[/bold]")
    console.print("[dim](Press Ctrl+D or Ctrl+Z when done)[/dim]\n")

    job_description_lines = []
    try:
        while True:
            line = input()
            job_description_lines.append(line)
    except EOFError:
        pass

    job_description = "\n".join(job_description_lines).strip()

    if not job_description:
        console.print("[red]Error: Job description is required[/red]")
        raise typer.Exit(1)

    # Initialize agent
    console.print("\n[yellow]Initializing AI agent...[/yellow]")
    try:
        agent = ApplicationAgent(provider=provider or "auto")
        status = agent.get_status()
        console.print(f"[dim]  Active Provider: {status['active_provider']}[/dim]")
        available = [p for p, v in status['available_providers'].items() if v]
        console.print(f"[dim]  Available: {', '.join(available)}[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Analyze job fit (uses local keyword matching, fast and free)
    console.print("[yellow]Analyzing job fit...[/yellow]")
    try:
        fit_analysis = agent.analyze_job_fit(job_description)

        analysis_type = fit_analysis.get('analysis_type', 'unknown')
        console.print(f"\n[bold]Fit Analysis[/bold] [dim]({analysis_type})[/dim]:")
        console.print(f"  Score: [cyan]{fit_analysis.get('fit_score', 'N/A')}/10[/cyan]")
        console.print(f"  Recommendation: [cyan]{fit_analysis.get('recommendation', 'N/A')}[/cyan]")
        console.print(f"  Reasoning: {fit_analysis.get('reasoning', 'N/A')}")

        if fit_analysis.get('strengths'):
            console.print(f"\n  [green]Strengths:[/green]")
            for strength in fit_analysis['strengths'][:8]:  # Limit display
                console.print(f"    ✓ {strength}")

        if fit_analysis.get('gaps'):
            console.print(f"\n  [yellow]Gaps:[/yellow]")
            for gap in fit_analysis['gaps'][:5]:  # Limit display
                console.print(f"    - {gap}")

        if fit_analysis.get('cloud_error'):
            console.print(f"\n  [dim]Note: Using local analysis (cloud unavailable)[/dim]")

    except Exception as e:
        console.print(f"[yellow]Warning: Could not analyze fit: {e}[/yellow]")

    # Ask if should continue
    if not Confirm.ask("\n[bold]Generate cover letter?[/bold]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit(0)

    # Generate cover letter
    console.print("\n[yellow]Generating cover letter...[/yellow]")
    try:
        cover_letter = agent.generate_cover_letter(company, role, job_description)

        console.print("\n" + "="*60)
        console.print(cover_letter)
        console.print("="*60 + "\n")

    except Exception as e:
        console.print(f"[red]Error generating cover letter: {e}[/red]")
        raise typer.Exit(1)

    # Ask if should save
    if Confirm.ask("[bold]Save this application?[/bold]", default=True):
        # Save to database
        try:
            app_record = add_application(
                company=company,
                role=role,
                job_url=job_url if job_url else None,
                job_description=job_description,
                status="Applied",
                notes=f"Cover letter generated on {datetime.now().strftime('%Y-%m-%d')}"
            )

            console.print(f"\n[green]✓ Application saved to database (ID: {app_record.id})[/green]")

            # Optionally save cover letter to file
            if Confirm.ask("[bold]Save cover letter to file?[/bold]", default=True):
                cover_letters_dir = Path("data/cover_letters")
                filename = f"Philipp_Goetting_Cover_Letter_{company.replace(' ', '_')}.txt"
                filepath = cover_letters_dir / filename

                filepath.write_text(cover_letter)
                console.print(f"[green]✓ Cover letter saved to: {filepath}[/green]")

        except Exception as e:
            console.print(f"[red]Error saving: {e}[/red]")
            raise typer.Exit(1)

    console.print("\n[bold green]Done! 🎉[/bold green]\n")


@app.command()
def list(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
):
    """
    List your job applications.
    """
    console.print("\n[bold cyan]📋 Your Applications[/bold cyan]\n")

    try:
        applications = get_applications(status=status, limit=limit)

        if not applications:
            console.print("[yellow]No applications found[/yellow]")
            return

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Company")
        table.add_column("Role")
        table.add_column("Status")
        table.add_column("Applied", style="dim")

        for app in applications:
            table.add_row(
                str(app.id),
                app.company,
                app.role,
                app.status,
                app.application_date.strftime("%Y-%m-%d") if app.application_date else "N/A"
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats():
    """
    Show application statistics.
    """
    console.print("\n[bold cyan]📊 Application Statistics[/bold cyan]\n")

    try:
        stats = get_application_stats()

        console.print(f"[bold]Total Applications:[/bold] {stats['total']}")
        console.print(f"  Applied: [cyan]{stats['applied']}[/cyan]")
        console.print(f"  Interview: [green]{stats['interview']}[/green]")
        console.print(f"  Rejected: [red]{stats['rejected']}[/red]")
        console.print(f"  Offer: [yellow]{stats['offer']}[/yellow]")
        console.print(f"  Accepted: [bold green]{stats['accepted']}[/bold green]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def screen():
    """
    Quick local screening of a job (no API needed, free and fast).

    Paste a job description and get instant fit analysis using keyword matching.
    """
    console.print("\n[bold cyan]🔍 Quick Job Screener (Local)[/bold cyan]")
    console.print("[dim]No API calls - instant results[/dim]\n")

    # Get job description
    console.print("[bold]Paste the job description below[/bold]")
    console.print("[dim](Press Ctrl+D or Ctrl+Z when done)[/dim]\n")

    job_description_lines = []
    try:
        while True:
            line = input()
            job_description_lines.append(line)
    except EOFError:
        pass

    job_description = "\n".join(job_description_lines).strip()

    if not job_description:
        console.print("[red]Error: Job description is required[/red]")
        raise typer.Exit(1)

    # Use local analyzer directly
    from tools.local_analyzer import analyze_job_fit_local

    console.print("\n[yellow]Analyzing...[/yellow]")
    result = analyze_job_fit_local(job_description)

    # Display results
    score = result.get('fit_score', 0)
    rec = result.get('recommendation', 'Unknown')

    # Color based on score
    if score >= 7:
        score_color = "green"
    elif score >= 5:
        score_color = "yellow"
    else:
        score_color = "red"

    console.print(f"\n[bold]Result:[/bold]")
    console.print(f"  Score: [{score_color}]{score}/10[/{score_color}]")
    console.print(f"  Recommendation: [{score_color}]{rec}[/{score_color}]")

    tech_matches = result.get('technical_matches', [])
    tech_gaps = result.get('technical_gaps', [])
    biz_matches = result.get('business_matches', [])

    if tech_matches:
        console.print(f"\n[green]✓ Technical Skills Matched ({len(tech_matches)}):[/green]")
        console.print(f"  {', '.join(tech_matches[:10])}")

    if biz_matches:
        console.print(f"\n[green]✓ Business Skills Matched ({len(biz_matches)}):[/green]")
        console.print(f"  {', '.join(biz_matches[:8])}")

    if tech_gaps:
        console.print(f"\n[yellow]✗ Skills to Highlight/Learn ({len(tech_gaps)}):[/yellow]")
        console.print(f"  {', '.join(tech_gaps[:8])}")

    # Quick recommendation
    console.print("\n" + "─"*50)
    if score >= 7:
        console.print("[bold green]→ Worth applying! Run 'python3 cli/main.py apply' to generate cover letter[/bold green]")
    elif score >= 5:
        console.print("[bold yellow]→ Reasonable fit. Consider applying if interested in the company.[/bold yellow]")
    else:
        console.print("[bold red]→ Weak fit. Focus on jobs matching more of your skills.[/bold red]")

    console.print()


@app.command()
def status():
    """
    Show AI agent status and available providers.
    """
    console.print("\n[bold cyan]🤖 AI Agent Status[/bold cyan]\n")

    try:
        agent = ApplicationAgent(provider="auto")
        status = agent.get_status()

        console.print(f"[bold]Active Provider:[/bold] {status['active_provider']}")
        console.print(f"[bold]CV Loaded:[/bold] {'✓ Yes' if status['cv_loaded'] else '✗ No'}")

        console.print(f"\n[bold]Available Providers:[/bold]")
        for provider, available in status['available_providers'].items():
            icon = "[green]✓[/green]" if available else "[red]✗[/red]"
            desc = {
                'local': 'Keyword matching (free, offline)',
                'groq': 'Llama 3.3 70B (free tier)',
                'google': 'Gemini 1.5 Flash (free tier)',
                'openai': 'GPT-4o-mini (paid)'
            }.get(provider, '')
            console.print(f"  {icon} {provider}: {desc}")

        console.print(f"\n[bold]Usage:[/bold]")
        console.print(f"  python3 cli/main.py apply --provider groq")
        console.print(f"  python3 cli/main.py apply --provider google")
        console.print(f"  python3 cli/main.py screen  [dim](always uses local)[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print()


@app.command()
def scan():
    """
    Scan inbox for new job opportunities (placeholder).
    """
    print("[bold green]Scanning inbox (placeholder)...[/bold green]")


@app.command()
def ui():
    """
    Launch the Streamlit UI.
    """
    print("Starting Streamlit UI...")
    import subprocess
    subprocess.run(["streamlit", "run", "ui/app.py"])


if __name__ == "__main__":
    app()

