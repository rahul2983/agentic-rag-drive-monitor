#!/usr/bin/env python3
"""
Scheduler and Configuration Management for Agentic RAG Drive Monitor
Handles weekly scheduling, configuration management, and advanced features.
"""

import os
import json
import time
import schedule
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import logging
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Import our main application
from main import AgenticRAGApplication, DocumentMetadata, ActionItem

@dataclass
class AppConfig:
    """Application configuration management"""
    google_credentials_path: str
    google_token_path: str
    openai_api_key: str
    scan_interval_hours: int = 168  # Default to weekly
    email_notifications: bool = False
    email_host: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    default_timezone: str = "America/New_York"
    log_level: str = "INFO"
    vector_db_path: str = "./simple_db"  # Updated from chroma_db
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

class ConfigManager:
    """Manages application configuration from environment and files"""
    
    @staticmethod
    def load_config() -> AppConfig:
        """Load configuration from environment variables and .env file"""
        load_dotenv()
        
        # Extract email recipients from comma-separated string
        email_recipients = []
        recipients_str = os.getenv('EMAIL_RECIPIENTS', '')
        if recipients_str:
            email_recipients = [email.strip() for email in recipients_str.split(',')]
        
        return AppConfig(
            google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json'),
            google_token_path=os.getenv('GOOGLE_TOKEN_PATH', './token.json'),
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            scan_interval_hours=int(os.getenv('SCAN_INTERVAL_HOURS', '168')),  # Default to weekly
            email_notifications=os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
            email_host=os.getenv('EMAIL_HOST', 'smtp.gmail.com'),
            email_port=int(os.getenv('EMAIL_PORT', '587')),
            email_username=os.getenv('EMAIL_USERNAME', ''),
            email_password=os.getenv('EMAIL_PASSWORD', ''),
            email_recipients=email_recipients,
            default_timezone=os.getenv('DEFAULT_TIMEZONE', 'America/New_York'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            vector_db_path=os.getenv('VECTOR_DB_PATH', './simple_db')  # Updated from chroma_db
        )
    
    @staticmethod
    def validate_config(config: AppConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not config.openai_api_key:
            errors.append("OpenAI API key is required")
        
        if not Path(config.google_credentials_path).exists():
            errors.append(f"Google credentials file not found: {config.google_credentials_path}")
        
        if config.email_notifications:
            if not config.email_username or not config.email_password:
                errors.append("Email credentials required for notifications")
            if not config.email_recipients:
                errors.append("Email recipients required for notifications")
        
        return errors

class EmailNotifier:
    """Handles email notifications for weekly summaries"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def send_weekly_summary(self, summary_content: str, docs: List[DocumentMetadata], actions: List[ActionItem]):
        """Send formatted weekly summary via email"""
        if not self.config.email_notifications:
            return
        
        try:
            # Create HTML email content
            html_content = self.create_html_summary(summary_content, docs, actions)
            
            # Setup email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Google Drive Weekly Summary - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            
            # Add both plain text and HTML versions
            msg.attach(MIMEText(summary_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config.email_host, self.config.email_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            self.logger.info("Weekly summary email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email summary: {e}")
    
    def create_html_summary(self, summary_content: str, docs: List[DocumentMetadata], actions: List[ActionItem]) -> str:
        """Create HTML formatted email summary"""
        
        # Count documents by priority
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for doc in docs:
            priority_counts[doc.priority] = priority_counts.get(doc.priority, 0) + 1
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #4285f4; color: white; padding: 20px; border-radius: 5px; }}
                .summary-stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .priority-high {{ border-left: 5px solid #ea4335; }}
                .priority-medium {{ border-left: 5px solid #fbbc04; }}
                .priority-low {{ border-left: 5px solid #34a853; }}
                .document-card {{ margin: 15px 0; padding: 15px; border: 1px solid #eee; border-radius: 5px; }}
                .action-item {{ background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Google Drive Weekly Summary</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="summary-stats">
                <div class="stat-box">
                    <h3>{len(docs)}</h3>
                    <p>New Documents</p>
                </div>
                <div class="stat-box">
                    <h3>{len(actions)}</h3>
                    <p>Action Items</p>
                </div>
                <div class="stat-box">
                    <h3>{priority_counts['high']}</h3>
                    <p>High Priority</p>
                </div>
            </div>
            
            <h2>Document Details</h2>
        """
        
        for doc in docs:
            priority_class = f"priority-{doc.priority}"
            html += f"""
            <div class="document-card {priority_class}">
                <h3>{doc.name}</h3>
                <p><strong>Priority:</strong> {doc.priority.upper()}</p>
                <p><strong>Summary:</strong> {doc.content_summary}</p>
                
                {f'<h4>Action Items ({len(doc.action_items)}):</h4>' if doc.action_items else ''}
                {''.join([f'<div class="action-item">• {item}</div>' for item in doc.action_items])}
                
                {f'<h4>Follow-ups ({len(doc.follow_ups)}):</h4>' if doc.follow_ups else ''}
                {''.join([f'<div class="action-item">• {item}</div>' for item in doc.follow_ups])}
            </div>
            """
        
        html += """
            </body>
        </html>
        """
        
        return html

class AdvancedScheduler:
    """Advanced scheduling with multiple triggers and monitoring"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.app = None
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self.email_notifier = EmailNotifier(config)
        self.last_run = None
        self.run_count = 0
        
    def initialize_app(self):
        """Initialize the main application"""
        try:
            app_config = {
                'google_credentials_path': self.config.google_credentials_path,
                'google_token_path': self.config.google_token_path,
                'openai_api_key': self.config.openai_api_key,
                'email_notifications': self.config.email_notifications
            }
            
            self.app = AgenticRAGApplication(app_config)
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def run_scheduled_scan(self):
        """Run the scheduled scan with enhanced monitoring"""
        start_time = datetime.now()
        self.run_count += 1
        
        self.console.print(f"\n[bold blue]Starting Scan #{self.run_count}[/bold blue]")
        self.console.print(f"[dim]Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        
        try:
            with Progress() as progress:
                task = progress.add_task("[green]Processing documents...", total=100)
                
                # Initialize app if needed
                if not self.app:
                    self.initialize_app()
                
                progress.update(task, advance=20)
                
                # Run the scan (now weekly by default)
                await self.app.run_daily_scan()
                
                progress.update(task, advance=60)
                
                # Send notifications if enabled
                if self.config.email_notifications:
                    # Load processed documents for email
                    await self.send_notifications()
                
                progress.update(task, advance=20)
            
            self.last_run = start_time
            duration = datetime.now() - start_time
            
            self.console.print(f"[bold green]✓ Scan completed successfully[/bold green]")
            self.console.print(f"[dim]Duration: {duration.total_seconds():.1f} seconds[/dim]")
            
            # Log statistics
            self.log_run_statistics(duration)
            
        except Exception as e:
            self.logger.error(f"Scheduled scan failed: {e}")
            self.console.print(f"[bold red]✗ Scan failed: {e}[/bold red]")
    
    async def send_notifications(self):
        """Send email notifications for the latest scan"""
        try:
            # Load the latest summary (now weekly)
            today = datetime.now().strftime('%Y%m%d')
            summary_file = f"daily_summary_{today}.md"
            
            if Path(summary_file).exists():
                with open(summary_file, 'r') as f:
                    summary_content = f.read()
                
                # For now, send the markdown content
                # In a full implementation, we'd reconstruct the document and action lists
                await self.email_notifier.send_weekly_summary(summary_content, [], [])
            
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")
    
    def log_run_statistics(self, duration):
        """Log detailed run statistics"""
        stats = {
            'run_number': self.run_count,
            'start_time': self.last_run.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'status': 'success'
        }
        
        # Save to stats file
        stats_file = Path('run_statistics.json')
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
        """Setup various scheduling options"""

        # Weekly schedule (every Monday at 9:00 AM)
        schedule.every().monday.at("09:00").do(lambda: asyncio.run(self.run_scheduled_scan()))
        
        # Optional: Additional schedules based on configuration
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
            schedule_type = "weekly"
        elif self.config.scan_interval_hours >= 24:
            schedule_type = f"every {self.config.scan_interval_hours // 24} day(s)"
        else:
            schedule_type = f"every {self.config.scan_interval_hours} hour(s)"
        
        self.logger.info(f"Schedules configured successfully - {schedule_type}")
    
    async def generate_monthly_summary(self):
        """Generate monthly summary report (replaces weekly summary since we're now running weekly)"""
        try:
            self.logger.info("Generating monthly summary...")
            
            # Load last 30 days of summaries
            monthly_content = f"# Monthly Google Drive Summary\n"
            monthly_content += f"Month ending: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            
            total_docs = 0
            total_actions = 0
            
            for i in range(30):  # Last 30 days
                date = datetime.now() - timedelta(days=i)
                summary_file = f"daily_summary_{date.strftime('%Y%m%d')}.md"
                
                if Path(summary_file).exists():
                    with open(summary_file, 'r') as f:
                        content = f.read()
                        # Parse document and action counts from content
                        if "New Documents Processed:" in content:
                            try:
                                doc_count = int(content.split("New Documents Processed: ")[1].split("\n")[0])
                                total_docs += doc_count
                            except:
                                pass
            
            monthly_content += f"## Monthly Statistics\n"
            monthly_content += f"- Total Documents Processed: {total_docs}\n"
            monthly_content += f"- Total Action Items Created: {total_actions}\n\n"
            
            # Save monthly summary
            monthly_file = f"monthly_summary_{datetime.now().strftime('%Y_%m')}.md"
            with open(monthly_file, 'w') as f:
                f.write(monthly_content)
            
            self.logger.info(f"Monthly summary saved to {monthly_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate monthly summary: {e}")
    
    def display_status_table(self):
        """Display current status in a nice table"""
        table = Table(title="Agentic RAG Monitor Status")
    
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
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
        
        self.console.print(table)
    
    def run_scheduler(self):
        """Main scheduler loop"""
        self.console.print("[bold blue]🚀 Agentic RAG Drive Monitor Starting...[/bold blue]")
        
        # Validate configuration
        config_errors = ConfigManager.validate_config(self.config)
        if config_errors:
            self.console.print("[bold red]Configuration Errors:[/bold red]")
            for error in config_errors:
                self.console.print(f"  ❌ {error}")
            return
        
        # Setup schedules
        self.setup_schedules()
        
        # Display initial status
        self.display_status_table()
        
        self.console.print("\n[bold green]✓ Scheduler started successfully[/bold green]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Run scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]⚠️  Scheduler stopped by user[/bold yellow]")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            self.console.print(f"[bold red]❌ Scheduler error: {e}[/bold red]")

class CLIManager:
    """Command-line interface for manual operations"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.scheduler = AdvancedScheduler(config)
        self.console = Console()
    
    async def run_manual_scan(self):
        """Run a manual scan immediately"""
        self.console.print("[bold blue]Running manual scan...[/bold blue]")
        await self.scheduler.run_scheduled_scan()
    
    def show_statistics(self):
        """Show detailed statistics"""
        stats_file = Path('run_statistics.json')
        
        if not stats_file.exists():
            self.console.print("[yellow]No statistics available yet[/yellow]")
            return
        
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        if not stats:
            self.console.print("[yellow]No statistics available yet[/yellow]")
            return
        
        # Create statistics table
        table = Table(title="Run Statistics (Last 10 runs)")
        table.add_column("Run #", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Status", style="magenta")
        
        for stat in stats[-10:]:  # Last 10 runs
            date = datetime.fromisoformat(stat['start_time']).strftime('%m/%d %H:%M')
            duration = f"{stat['duration_seconds']:.1f}s"
            status = "✅ Success" if stat['status'] == 'success' else "❌ Failed"
            
            table.add_row(
                str(stat['run_number']),
                date,
                duration,
                status
            )
        
        self.console.print(table)
        
        # Summary statistics
        avg_duration = sum(s['duration_seconds'] for s in stats) / len(stats)
        success_rate = sum(1 for s in stats if s['status'] == 'success') / len(stats) * 100
        
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Total runs: {len(stats)}")
        self.console.print(f"  Average duration: {avg_duration:.1f} seconds")
        self.console.print(f"  Success rate: {success_rate:.1f}%")

def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic RAG Drive Monitor - Weekly Scheduler")
    parser.add_argument('--mode', choices=['schedule', 'scan', 'stats'], 
                       default='schedule', help='Run mode')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = ConfigManager.load_config()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('drive_monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create CLI manager
    cli = CLIManager(config)
    
    if args.mode == 'schedule':
        # Run scheduler
        cli.scheduler.run_scheduler()
        
    elif args.mode == 'scan':
        # Run manual scan
        asyncio.run(cli.run_manual_scan())
        
    elif args.mode == 'stats':
        # Show statistics
        cli.show_statistics()

if __name__ == "__main__":
    main()