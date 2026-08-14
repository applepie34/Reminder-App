from plyer import notification as notif
import playsound
import questionary as qs
from rich.console import Console
from rich.table import Table
import sql
from datetime import datetime, timedelta
import calendar
import threading
import time
import os
import subprocess
import sys

console = Console()


def display_all_task():
    tasks = sql.get_reminders()
    if not tasks:
        console.print("[yellow]No reminders found.[/yellow]")
        return

    table = Table(title="Reminder")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Task title", style="cyan")
    table.add_column("Desc", style="cyan")
    table.add_column("Recurrence", style="cyan")
    table.add_column("Date", style="cyan")
    table.add_column("Time", style="cyan", justify="center")
    for task in tasks:
        table.add_row(str(task[0]), str(task[1]), str(task[2]), str(task[3]), str(task[4]), str(task[5]))
    console.print(table)


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
    date_str = ""
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


def display_top_3_closest():
    now = datetime.now()
    tasks = sql.get_reminders()
    if not tasks:
        return

    upcoming_tasks = []
    for task in tasks:
        recurrence, task_date_str, task_time_str, task_title = task[3], task[4], task[5], task[1]
        next_due = get_next_due_datetime(recurrence, task_date_str, task_time_str, now)
        if next_due and next_due >= now:
            time_difference = next_due - now
            upcoming_tasks.append((time_difference, task_title, next_due))

    if upcoming_tasks:
        upcoming_tasks.sort(key=lambda x: x[0])
        top_3 = upcoming_tasks[:3]

        console.print("\n[bold yellow]⏳ Top 3 Closest Reminders:[/bold yellow]")
        for diff, title, due_time in top_3:
            time_left = str(diff).split(".")[0]
            console.print(
                f"• [cyan]{title}[/cyan] -> Due: [magenta]{due_time.strftime('%Y-%m-%d %H:%M')}[/magenta] (in [green]{time_left}[/green])"
            )
        console.print()


def get_next_due_datetime(recurrence: str, task_date_str: str, task_time_str: str, now: datetime) -> datetime:
    rec = recurrence.lower()

    try:
        task_time = datetime.strptime(task_time_str, "%H:%M").time()
    except ValueError:
        return None

    if rec == "daily":
        next_due = datetime.combine(now.date(), task_time)
        if next_due < now:
            next_due += timedelta(days=1)
        return next_due

    elif rec == "once":
        try:
            task_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
            return datetime.combine(task_date, task_time)
        except ValueError:
            return None

    elif rec == "weekly":
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if task_date_str.lower() not in days_of_week:
            return None

        target_weekday = days_of_week.index(task_date_str.lower())
        days_ahead = target_weekday - now.weekday()

        if days_ahead < 0 or (days_ahead == 0 and datetime.combine(now.date(), task_time) < now):
            days_ahead += 7

        next_date = now.date() + timedelta(days=days_ahead)
        return datetime.combine(next_date, task_time)

    elif rec == "monthly":
        try:
            target_day = int(task_date_str)
        except ValueError:
            return None

        year, month = now.year, now.month
        max_days = calendar.monthrange(year, month)[1]
        clamped_day = min(target_day, max_days)
        next_due = datetime.combine(datetime(year, month, clamped_day).date(), task_time)

        if next_due < now:
            month += 1
            if month > 12:
                month = 1
                year += 1
            max_days = calendar.monthrange(year, month)[1]
            clamped_day = min(target_day, max_days)
            next_due = datetime.combine(datetime(year, month, clamped_day).date(), task_time)

        return next_due

    elif rec == "yearly":
        try:
            target_month, target_day = map(int, task_date_str.split("-"))
        except (ValueError, AttributeError):
            return None

        year = now.year
        max_days = calendar.monthrange(year, target_month)[1]
        clamped_day = min(target_day, max_days)
        next_due = datetime.combine(datetime(year, target_month, clamped_day).date(), task_time)

        if next_due < now:
            year += 1
            max_days = calendar.monthrange(year, target_month)[1]
            clamped_day = min(target_day, max_days)
            next_due = datetime.combine(datetime(year, target_month, clamped_day).date(), task_time)

        return next_due

    return None


def check_due_reminders(now: datetime):
    tasks = sql.get_reminders()

    if not tasks:
        return

    current_minute_str = now.strftime("%Y-%m-%d %H:%M")

    for task in tasks:
        task_id, task_title, task_desc, recurrence, task_date_str, task_time_str = task

        next_due = get_next_due_datetime(recurrence, task_date_str, task_time_str, now)
        if next_due and next_due.strftime("%Y-%m-%d %H:%M") == current_minute_str:

            notif.notify(
                            title=f"Reminder: {task_title}",
                            message=task_desc,
                            app_name="Reminders",
                            timeout=10,
                        )


            try:
                sound_path = get_resource_path("alert.mp3")
                playsound.playsound(sound_path)
            except Exception:
                pass

            

            if recurrence.lower() == "once":
                sql.delete_reminder(task_id)


def start_background_thread():
    last_checked_minute = ""
    while True:
        now = datetime.now()
        current_minute = now.strftime("%Y-%m-%d %H:%M")

        if current_minute != last_checked_minute:
            check_due_reminders(now)
            last_checked_minute = current_minute

        time.sleep(1)


def delete_task():
    display_all_task()
    task_id_str = qs.text("Enter the ID of the reminder to delete:").ask()

    if not task_id_str or not task_id_str.isdigit():
        console.print("[red]Invalid ID provided![/red]\n")
        return

    sql.delete_reminder(int(task_id_str))
    console.print(f"[bold green]✔ Reminder ID {task_id_str} deleted successfully![/bold green]\n")


def clear_screen():
    
    command = "cls" if os.name == "nt" else "clear"
    subprocess.run(command, shell=True)


def get_resource_path(relative_path: str) -> str:
   
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def run_menu():
    sql.get_connection()
    sql.init_db()

    monitor_thread = threading.Thread(target=start_background_thread, daemon=True)
    monitor_thread.start()

    while True:
        clear_screen()

        action = qs.select(
            "Use ARROW KEYS to choose an option:",
            choices=[
                "View Reminders",
                "View Top 3 Closest Reminders",
                "Add Reminder",
                "Delete Reminder",
                "Exit",
            ],
        ).ask()
        clear_screen()
        if action == "View Reminders":
            display_all_task()
            input("\nPress Enter to continue...")

        elif action == "View Top 3 Closest Reminders":
            display_top_3_closest()
            input("\nPress Enter to continue...")

        elif action == "Add Reminder":
            add_new_task()
            time.sleep(1.5)

        elif action == "Delete Reminder":
            delete_task()
            time.sleep(1.5)

        elif action == "Exit":
            console.print("[bold red]Goodbye![/bold red]")
            break


if __name__ == "__main__":
    run_menu()