from plyer import notification as notif
import playsound
import questionary as qs
from rich.console import Console
from rich.table import Table
import sql
from datetime import datetime,timedelta
import calendar
import threading

console = Console()


def display_all_task():
    tasks = sql.get_reminders()
    if not tasks:
        console.print("[yellow]No reminders found.[/yellow]")
        return

    table = Table(title= "Reminder")
    table.add_column("ID",style = "cyan",justify = "center")
    table.add_column("Task title",style = "cyan")
    table.add_column("Desc",style = "cyan")
    table.add_column("Recurrence",style = "cyan")
    table.add_column("Date",style = "cyan")
    table.add_column("Time",style = "cyan", justify = "center")
    for task in tasks:
        table.add_row(str(task[0]),task[1],task[2],task[3],task[4],task[5])
    console.print(table)

def should_trigger(recurrence: str, task_date_str: str, now: datetime) -> bool:
    rec = recurrence.lower()

    
    if rec == "daily":
        return True

    
    try:
        task_date = datetime.strptime(task_date_str, "%Y-%m-%d")
    except ValueError:
        return False

    today = now.date()

    
    if rec == "once":
        return today == task_date.date()

    
    elif rec == "weekly":
        return today.weekday() == task_date.weekday()

    
    elif rec == "monthly":
        
        max_days = calendar.monthrange(today.year, today.month)[1]
        target_day = min(task_date.day, max_days)

        return today.day == target_day

    
    elif rec == "yearly":
        
        target_month = task_date.month
        max_days = calendar.monthrange(today.year, target_month)[1]
        target_day = min(task_date.day, max_days)

        return (today.month == target_month) and (today.day == target_day)

    return False


def add_new_task():
    console.print("\n[bold green]-- Create New Reminder -- [/bold green]")
    title = qs.text("Enter reminder title:").ask()
    if not title:
        console.print("[red]Title cannot be empty![/red]\n")
        return

    description = qs.text("Enter description (optional):").ask()
    if not description:
        description = "reminder"
    recurrence = qs.select(
        "Select recurrence pattern:",
        choices=["once", "daily", "weekly", "monthly", "yearly"]
    ).ask()

    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    default_date = tomorrow.strftime("%Y-%m-%d")
    default_time = now.strftime("%H:%M")
    date_str =""
    if recurrence == "once":
        date_str = qs.text(f"Enter date (YYYY-MM-DD) [{default_date}]:").ask()
        if not date_str:
            date_str = default_date

    elif recurrence == "weekly":
        date_str = qs.select(
            "Select day of the week:",
            choices=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ).ask()

    elif recurrence == "monthly":
        date_str = qs.text("Enter day of the month (1-31):").ask()
        if not date_str:
            date_str = "1"

    elif recurrence == "yearly":
        default_mmdd = tomorrow.strftime("%m-%d")
        date_str = qs.text(f"Enter month & day (MM-DD) [{default_mmdd}]:").ask()
        if not date_str:
            date_str = default_mmdd

    elif recurrence == "daily":
        date_str = "Everyday"
    default_time = now.strftime("%H:%M")
    time_str = qs.text(f"Enter time (HH:MM) [{default_time}]:").ask()

    if not time_str:
        time_str = default_time

    sql.add_reminder(title, description, recurrence, date_str, time_str)

    console.print(f"[bold green]✔ Reminder '{title}' saved successfully![/bold green]\n")


add_new_task()