import ntpath
import os
import sys
import traceback
from datetime import datetime

from common import mail_sender
from common.logger import Logger
import psutil


def avoid_robot_duplicate():
    if getattr(sys, 'frozen', False):
        processes = []
        for process in psutil.process_iter():
            try:
                processes.append(process.name().lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return processes.count(ntpath.basename(sys.executable)) > 2

    return False


def send_error(message, settings, robot_name):
    subject = f"Blad robota {robot_name}"

    mail_sender.send_email(subject, message, settings["target_emails"]["robot_email"], settings)


def save_report(report):
    script_path = os.getcwd()
    dir_path = os.path.join(script_path, "raporty")
    filename = f"raport_{datetime.now().strftime('%Y_%m_%d %H_%M_%S')}.txt"
    path = os.path.join(dir_path, filename)

    try:
        with open(path, "a") as file:
            file.write(report)
    except Exception as error:
        Logger.error(f"Save report error: {error}")
        Logger.error(traceback.format_exc())


def send_report(report, settings, robot_name):
    subject_short_report = f"udanych:{report['successes_count']} bledow:{report['failures_count']}"
    subject = f"Raport robota {robot_name} {subject_short_report} "

    mail_sender.send_email(subject, report["report"], settings["target_emails"]["robot_email"], settings)
