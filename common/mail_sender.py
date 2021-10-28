import smtplib
import ssl
import re

from common.logger import Logger


def get_server_and_email(email):
    try:
        result = re.match("^(.*?)@(.*?)$", email)

        return {
            "login": result.group(1),
            "server": result.group(2),
        }

    except Exception as error:
        raise Exception(f"Blad podczas wczytywania emaila '{email}'! {error}", True)


def send_email(subject, message, receiver_email, settings):
    try:
        Logger.info(f"Wysylam wiadomosc do {receiver_email}")

        full_msg = f"Subject: {subject}\n{message}"
        email_data = settings["email_data"]
        email_search_data = get_server_and_email(email_data["email"])

        context = ssl.create_default_context()
        server = smtplib.SMTP(email_search_data["server"], 587)
        server.starttls(context=context)
        server.login(email_search_data["login"], email_data["password"])
        server.sendmail(email_data["email"], receiver_email, full_msg.encode('utf-8'))
        server.quit()
    except Exception as error:
        Logger.error(f"Blad podczas wysylania emaila! {error}")
