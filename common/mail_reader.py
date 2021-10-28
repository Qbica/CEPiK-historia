import email
import email.header
import imaplib
import os
import time

from common import mail_sender
from common.logger import Logger


class EmailReader:

    def __init__(self, settings):
        email_data = settings["email_data"]
        server_and_email = mail_sender.get_server_and_email(email_data["email"])
        self.login = server_and_email["login"]
        self.password = email_data["password"]
        self.host = server_and_email["server"]
        self.server = imaplib.IMAP4_SSL(host=self.host)

    def connect(self):
        try:
            self.server.login(self.login, self.password)

        except Exception as error:
            msg = f"Blad podczas logowania do maila: {self.login}. blad:{error}"
            Logger.error(msg)
            raise Exception(msg)

    def get_by_subject(self, subject):
        Logger.info(f"Szukanie maili z tytulem '{subject}'")

        self.server.select()

        _, search = self.server.search(None, f'(SUBJECT "{subject}")')

        messages = []

        for num in search[0].split():
            typ, data = self.server.fetch(num, '(RFC822)')

            for response_part in data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    email_message = email.message_from_string(raw_email.decode('utf-8'))
                    messages.append({"email_message": email_message, "uid": num})

        Logger.info(f"Znaleziono {len(messages)} maili z tytulem '{subject}'")

        return messages

    @staticmethod
    def download_attachment(email_message, path):
        Logger.info(f"Szukam zalacznika: {email_message['uid']}")

        for part in email_message["email_message"].walk():

            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()

            if not filename or ".csv" not in filename:
                continue

            Logger.info(f"Znalezino zalacznik {filename}")

            filepath = os.path.join(path, f"{time.time()}_{filename}")
            with open(filepath, 'wb') as file:
                file.write(part.get_payload(decode=True))

            Logger.info(f"Pobrano {filepath}")

    @staticmethod
    def get_subject(mail):
        subject_byte = email.header.decode_header(mail["email_message"]['subject'])[0]

        return subject_byte[0].decode(subject_byte[1])

    @staticmethod
    def get_content(mail):
        for part in mail["email_message"].walk():
            if part.get_content_maintype() == 'text':
                return part.get_payload(decode=True).decode()

        return ""

    def delete_mail(self, email_message):
        try:
            Logger.info(f"Usuwam wiadomosc: {email_message['uid']}")
            self.server.store(email_message["uid"], "+FLAGS", "\\Deleted")
        except Exception as error:
            msg = f"Blad usuwania maila: {error}"
            Logger.error(msg)
            raise Exception(msg)

    def exit(self):
        self.server.expunge()
        self.server.close()
        self.server.logout()
