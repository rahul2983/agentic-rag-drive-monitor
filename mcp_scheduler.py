#!/usr/bin/env python3
"""
MCP-based Scheduler for Agentic RAG Drive Monitor
Orchestrates the entire workflow using MCP servers
"""

import asyncio
import json
import logging
import os
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# Import our MCP main application
from mcp_main_server import MCPAgenticRAGApplication

@dataclass
class MCPConfig:
    """Configuration for MCP-based Agentic RAG system"""
    google_credentials_path: str
    google_token_path: str
    openai_api_key: str
    target_folder_id: str = None
    target_folder_name: str = None
    include_subfolders: bool = True
    scan_interval_hours: int = 168  # Default to weekly
    email_notifications: bool = False
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    default_timezone: str = "America/New_York"
    log_level: str = "INFO"
    state_file_path: str = "./mcp_app_state.json"
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

class MCPConfigManager:
    """Manages MCP configuration from environment and files"""
    
    @staticmethod
    def load_config() -> MCPConfig:
        """Load configuration from environment variables and .env file"""
        load_dotenv()
        
        # Extract email recipients from comma-separated string
        email_recipients = []
        recipients_str = os.getenv('EMAIL_RECIPIENTS', '')
        if recipients_str:
            email_recipients = [email.strip() for email in recipients_str.split(',')]
        
        return MCPConfig(
            google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json'),
            google_token_path=os.getenv('GOOGLE_TOKEN_PATH', './token.json'),
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            target_folder_id=os.getenv('TARGET_FOLDER_ID'),
            target_folder_name=os.getenv('TARGET_FOLDER_NAME'),
            include_subfolders=os.getenv('INCLUDE_SUBFOLDERS', 'true').lower() == 'true',
            scan_interval_hours=int(os.getenv('SCAN_INTERVAL_HOURS', '168')),
            email_notifications=os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
            email_host=os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
            email_port=int(os.getenv('EMAIL_PORT', '587')),
            email_username=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            email_recipients=email_recipients,
            default_timezone=os.getenv('DEFAULT_TIMEZONE', 'America/New_York'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            state_file_path=os.getenv('STATE_FILE_PATH', './mcp_app_state.json')
        )
    
    @staticmethod
    def validate_config(config: MCPConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not config.openai_api_key:
            errors.append("OpenAI API key is required (OPENAI_API_KEY)")
        
        if not Path(config.google_credentials_path).exists():
            errors.append(f"Google credentials file not found: {config.google_credentials_path}")
        
        if config.email_notifications:
            if not config.email_username or not config.email_password:
                errors.append("Email credentials required for notifications (EMAIL_USERNAME, EMAIL_PASSWORD)")
            if not config.email_recipients:
                errors.append("Email recipients required for notifications (EMAIL_RECIPIENTS)")
        
        return errors

class MCPScheduler:
    """Advanced scheduler for MCP-based Agentic RAG system"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.app = None
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self.last_run = None
        self.run_count = 0
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mcp_agentic_rag.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize_app(self):
        """Initialize the MCP application"""
        try:
            app_config = {
                "google_credentials_path": self.config.google_credentials_path,
                "google_token_path": self.config.google_token_path,
                "openai_api_key": self.config.openai_api_key,
                "target_folder_id": self.config.target_folder_id,
                "email_notifications": self.config.email_notifications,
                "state_file_path": self.config.state_file_path
            }
            
            self.app = MCPAgenticRAGApplication(app_config)
            self.logger.info("MCP application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP application: {e}")
            raise
    
    async def run_scheduled_scan(self):
        """Run the scheduled agentic scan with enhanced monitoring"""
        start_time = datetime.now()
        self.run_count += 1
        
        self.console.print(f"\n[bold blue]Starting MCP Agentic Scan #{self.run_count}[/bold blue]")
        self.console.print(f"[dim]Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        
        try:
            with Progress() as progress:
                task = progress.add_task("[green]Initializing MCP servers...", total=100)
                
                # Initialize app if needed
                if not self.app:
                    self.initialize_app()
                
                progress.update(task, advance=20, description="[green]Connecting to MCP servers...")
                
                # Initialize MCP servers
                await self.app.initialize_mcp_servers()
                
                progress.update(task, advance=30, description="[green]Processing documents...")
                
                # Run the agentic scan
                await self.app.run_daily_scan()
                
                progress.update(task, advance=40, description="[green]Generating reports...")
                
                # Additional reporting if needed
                await self.generate_run_report()
                
                progress.update(task, advance=10, description="[green]Scan completed!")
            
            self.last_run = start_time
            duration = datetime.now() - start_time
            
            self.console.print(f"[bold green]✓ MCP Agentic Scan completed successfully[/bold green]")
            self.console.print(f"[dim]Duration: {duration.total_seconds():.1f} seconds[/dim]")
            
            # Log statistics
            self.log_run_statistics(duration)
            
        except Exception as e:
            self.logger.error(f"MCP scheduled scan failed: {e}")
            self.console.print(f"[bold red]✗ MCP Scan failed: {e}[/bold red]")
    
    async def generate_run_report(self):
        """Generate a detailed run report"""
        try:
            # Load task information from the orchestrator
            if self.app and self.app.orchestrator:
                completed_tasks = self.app.orchestrator.completed_tasks
                
                report = {
                    "run_id": self.run_count,
                    "timestamp": datetime.now().isoformat(),
                    "total_tasks": len(completed_tasks),
                    "successful_tasks": len([t for t in completed_tasks if t.status == "completed"]),
                    "failed_tasks": len([t for t in completed_tasks if t.status == "failed"]),
                    "task_breakdown": {}
                }
                
                # Categorize tasks by type
                for task in completed_tasks:
                    task_type = task.task_type
                    if task_type not in report["task_breakdown"]:
                        report["task_breakdown"][task_type] = {"completed": 0, "failed": 0}
                    
                    if task.status == "completed":
                        report["task_breakdown"][task_type]["completed"] += 1
                    else:
                        report["task_breakdown"][task_type]["failed"] += 1
                
                # Save report
                report_file = f"mcp_run_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                
                self.logger.info(f"Run report saved to {report_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate run report: {e}")
    
    def log_run_statistics(self, duration):
        """Log detailed run statistics"""
        stats = {
            'run_number': self.run_count,
            'start_time': self.last_run.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'status': 'success',
            'mcp_enabled': True
        }
        
        # Save to stats file
        stats_file = Path('mcp_run_statistics.json')
        all_stats = []
        
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                all_stats = json.load(f)
        
        all_stats.append(stats)
        
        # Keep only last 100 runs
        if len(all_stats) > 100:
            all_stats = all_stats[-100:]
        
        with open(stats_file, 'w') as f:
            json.dump(all_stats, f, indent=2)
    
    def setup_schedules(self):
        """Setup various scheduling options for MCP system"""
        
        # Weekly schedule (every Monday at 9:00 AM) - default for MCP version
        schedule.every().monday.at("09:00").do(lambda: asyncio.run(self.run_scheduled_scan()))
        
        # Additional schedules based on configuration
        if self.config.scan_interval_hours < 168:  # Less than weekly
            if self.config.scan_interval_hours >= 24:  # Daily or longer intervals
                if self.config.scan_interval_hours == 24:
                    # Daily scans
                    schedule.every().day.at("09:00").do(lambda: asyncio.run(self.run_scheduled_scan()))
                elif self.config.scan_interval_hours == 72:
                    # Every 3 days
                    schedule.every(3).days.at("09:00").do(lambda: asyncio.run(self.run_scheduled_scan()))
                else:
                    # Other multi-day intervals
                    schedule.every(self.config.scan_interval_hours).hours.do(
                        lambda: asyncio.run(self.run_scheduled_scan())
                    )
            else:
                # Hourly intervals (less than 24 hours)
                schedule.every(self.config.scan_interval_hours).hours.do(
                    lambda: asyncio.run(self.run_scheduled_scan())
                )
        
        # Monthly summary (first Sunday of month at 6 PM)
        schedule.every().sunday.at("18:00").do(lambda: asyncio.run(self.generate_monthly_summary()))
        
        # Determine schedule type for logging
        if self.config.scan_interval_hours >= 168:
            schedule_type = "weekly (MCP-optimized)"
        elif self.config.scan_interval_hours >= 24:
            schedule_type = f"every {self.config.scan_interval_hours // 24} day(s) (MCP-enabled)"
        else:
            schedule_type = f"every {self.config.scan_interval_hours} hour(s) (MCP-enabled)"
        
        self.logger.info(f"MCP schedules configured successfully - {schedule_type}")
    
    async def generate_monthly_summary(self):
        """Generate monthly summary report for MCP system"""
        try:
            self.logger.info("Generating MCP monthly summary...")
            
            # Load statistics from MCP runs
            stats_file = Path('mcp_run_statistics.json')
            if not stats_file.exists():
                self.logger.warning("No MCP run statistics found for monthly summary")
                return
            
            with open(stats_file, 'r') as f:
                all_stats = json.load(f)
            
            # Filter last 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_stats = [
                stat for stat in all_stats
                if datetime.fromisoformat(stat['start_time']) > cutoff_date
            ]
            
            if not recent_stats:
                self.logger.warning("No recent MCP statistics found for monthly summary")
                return
            
            # Generate summary
            total_runs = len(recent_stats)
            successful_runs = len([s for s in recent_stats if s['status'] == 'success'])
            avg_duration = sum(s['duration_seconds'] for s in recent_stats) / total_runs
            
            monthly_content = f"""# MCP Agentic RAG Monthly Summary

**Month ending:** {datetime.now().strftime('%Y-%m-%d')}

## System Performance (Last 30 Days)

- **Total Runs:** {total_runs}
- **Successful Runs:** {successful_runs}
- **Success Rate:** {(successful_runs/total_runs)*100:.1f}%
- **Average Duration:** {avg_duration:.1f} seconds
- **MCP Architecture:** Enabled

## MCP Server Performance

The system is running with modular MCP servers:
- Google Drive Server: Document retrieval and monitoring
- AI Analysis Server: Intelligent document processing
- Google Calendar Server: Automated event scheduling
- Email Server: Notification and summary delivery

## Architecture Benefits

- **Modularity:** Each function runs as independent MCP server
- **Scalability:** Servers can be independently updated and scaled
- **Reliability:** Isolated failures don't affect entire system
- **Extensibility:** New capabilities easily added as MCP servers

## Next Month Goals

- Monitor MCP server performance
- Optimize task orchestration
- Enhance agentic workflow capabilities
- Expand MCP server ecosystem
"""
            
            # Save monthly summary
            monthly_file = f"mcp_monthly_summary_{datetime.now().strftime('%Y_%m')}.md"
            with open(monthly_file, 'w') as f:
                f.write(monthly_content)
            
            self.logger.info(f"MCP monthly summary saved to {monthly_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate MCP monthly summary: {e}")
    
    def display_status_table(self):
        """Display current MCP system status in a nice table"""
        table = Table(title="MCP Agentic RAG Monitor Status")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("System Type", "🔗 MCP-based Architecture")
        table.add_row("Status", "🟢 Running" if self.app else "🔴 Not Started")
        table.add_row("Total Runs", str(self.run_count))
        table.add_row("Last Run", self.last_run.strftime('%Y-%m-%d %H:%M:%S') if self.last_run else "Never")
        table.add_row("Next Run", schedule.next_run().strftime('%Y-%m-%d %H:%M:%S') if schedule.jobs else "Not scheduled")
        
        # Enhanced schedule display
        if self.config.scan_interval_hours >= 168:
            schedule_text = "Weekly (Mondays at 9 AM)"
        elif self.config.scan_interval_hours >= 24:
            days = self.config.scan_interval_hours // 24
            schedule_text = f"Every {days} day{'s' if days > 1 else ''} at 9 AM"
        else:
            schedule_text = f"Every {self.config.scan_interval_hours} hours"
        
        table.add_row("Schedule", schedule_text)
        table.add_row("Scan Window", f"{self.config.scan_interval_hours} hours" if self.config.scan_interval_hours < 168 else "7 days (weekly)")
        table.add_row("Email Notifications", "✅ Enabled" if self.config.email_notifications else "❌ Disabled")
        table.add_row("MCP Servers", "🔗 Drive, AI, Calendar, Email")
        table.add_row("Target Folder", self.config.target_folder_name or "All Drive" if self.config.target_folder_name else "Not configured")
        
        self.console.print(table)
    
    def run_scheduler(self):
        """Main MCP scheduler loop"""
        self.console.print("[bold blue]🚀 MCP Agentic RAG Drive Monitor Starting...[/bold blue]")
        
        # Validate configuration
        config_errors = MCPConfigManager.validate_config(self.config)
        if config_errors:
            self.console.print("[bold red]Configuration Errors:[/bold red]")
            for error in config_errors:
                self.console.print(f"  ❌ {error}")
            return
        
        # Setup schedules
        self.setup_schedules()
        
        # Display initial status
        self.display_status_table()
        
        self.console.print("\n[bold green]✓ MCP Scheduler started successfully[/bold green]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Run scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]⚠️  MCP Scheduler stopped by user[/bold yellow]")
        except Exception as e:
            self.logger.error(f"MCP Scheduler error: {e}")
            self.console.print(f"[bold red]❌ MCP Scheduler error: {e}[/bold red]")

class MCPCLIManager:
    """Command-line interface for MCP manual operations"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.scheduler = MCPScheduler(config)
        self.console = Console()
    
    async def run_manual_scan(self):
        """Run a manual MCP scan immediately"""
        self.console.print("[bold blue]Running manual MCP scan...[/bold blue]")
        await self.scheduler.run_scheduled_scan()
    
    def show_statistics(self):
        """Show detailed MCP statistics"""
        stats_file = Path('mcp_run_statistics.json')
        
        if not stats_file.exists():
            self.console.print("[yellow]No MCP statistics available yet[/yellow]")
            return
        
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        if not stats:
            self.console.print("[yellow]No MCP statistics available yet[/yellow]")
            return
        
        # Create statistics table
        table = Table(title="MCP Run Statistics (Last 10 runs)")
        table.add_column("Run #", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Type", style="blue")
        
        for stat in stats[-10:]:  # Last 10 runs
            date = datetime.fromisoformat(stat['start_time']).strftime('%m/%d %H:%M')
            duration = f"{stat['duration_seconds']:.1f}s"
            status = "✅ Success" if stat['status'] == 'success' else "❌ Failed"
            system_type = "🔗 MCP" if stat.get('mcp_enabled') else "🔧 Legacy"
            
            table.add_row(
                str(stat['run_number']),
                date,
                duration,
                status,
                system_type
            )
        
        self.console.print(table)
        
        # Summary statistics
        avg_duration = sum(s['duration_seconds'] for s in stats) / len(stats)
        success_rate = sum(1 for s in stats if s['status'] == 'success') / len(stats) * 100
        mcp_runs = sum(1 for s in stats if s.get('mcp_enabled'))
        
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Total runs: {len(stats)}")
        self.console.print(f"  MCP-enabled runs: {mcp_runs}")
        self.console.print(f"  Average duration: {avg_duration:.1f} seconds")
        self.console.print(f"  Success rate: {success_rate:.1f}%")

def main():
    """Main CLI entry point for MCP system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Agentic RAG Drive Monitor")
    parser.add_argument('--mode', choices=['schedule', 'scan', 'stats'], 
                       default='schedule', help='Run mode')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = MCPConfigManager.load_config()
    
    # Create CLI manager
    cli = MCPCLIManager(config)
    
    if args.mode == 'schedule':
        # Run MCP scheduler
        cli.scheduler.run_scheduler()
        
    elif args.mode == 'scan':
        # Run manual MCP scan
        asyncio.run(cli.run_manual_scan())
        
    elif args.mode == 'stats':
        # Show MCP statistics
        cli.show_statistics()

if __name__ == "__main__":
    main()