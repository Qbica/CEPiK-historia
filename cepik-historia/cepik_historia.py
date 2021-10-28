import ntpath
import os
import sys
import traceback
from datetime import datetime

from common import file_manager, mail_sender
from common import robot_manager
from common.api.cepik_history.cepik_api import CepikAPI
from common.api.zordon.zordon_api import ZordonAPI
from common.api.zordon.zordon_helper import ZordonHelper
from common.excel import excel_read
from common.excel.cepik_history_settings import cepik_history_settings
from common.excel.cepik_history_settings import keeper_emails_settings
from common.logger import Logger


def get_fail_results_per_email(results):
    failures = [result for result in results if result["result"] == "error"]
    results_per_email = {}

    for result in failures:
        if "@" not in result["keeper_email"]:
            continue

        if result["keeper_email"] not in results_per_email:
            results_per_email[result["keeper_email"]] = []

        results_per_email[result["keeper_email"]].append(result)

    return results_per_email


def get_reports(results):
    results_per_email = get_fail_results_per_email(results)
    reports = {}
    date_now = datetime.now()

    for email, failures in results_per_email.items():
        failures_report_list = [
            f"Zlecenie:{result['order_number']}\nPowod:{result['reason']}"
            for result in failures]
        failures_report_string = "\n\n".join(failures_report_list)

        msg = f"Raport robota 'cepik-historia' {date_now}\n\n"
        msg += f"Lista bledow:\n{failures_report_string}\n\n"

        reports[email] = msg

    return reports


def get_robot_report(results):
    date_now = datetime.now()
    successes = [result for result in results if result["result"] == "ok"]
    failures = [result for result in results if result["result"] == "error"]

    successes_report_list = [result["order_number"] for result in successes]
    failures_report_list = [
        f"Zlecenie:{result['order_number']}\nPowod:{result['reason']} " \
        f"\nOpiekun:{result['keeper']}\nMail:{result['keeper_email']}"
        for result in failures]

    successes_report_string = "\n".join(successes_report_list)
    failures_report_string = "\n\n".join(failures_report_list)

    report = f"Raport robota 'cepik-historia' {date_now}\n\n"
    report += f"Ilosc zlecen: {len(results)}\n"
    report += f"Ilosc udanych: {len(successes)}\n"
    report += f"Ilosc bledow: {len(failures)}\n\n"

    if failures:
        report += f"Lista nieudanych:\n{failures_report_string}\n\n"

    if successes:
        report += f"Lista udanych:\n{successes_report_string}"

    return {
        "report": report,
        "successes_count": len(successes),
        "failures_count": len(failures),
        "date": date_now,
    }


def get_required_fields(order_details):
    required_fields = ["firstRegistrationAt", "registrationNumber", "vin"]
    translations = {
        "firstRegistrationAt": "Data pierwszej rejestracji",
        "registrationNumber": "Number rejestracyjny",
        "vin": "Vin",
    }
    issues = []
    car_data = {}

    for field in required_fields:
        value = order_details[field]

        if not value or len(value) == 0:
            issues.append(f"Brak wymaganego pola '{translations[field]}'")
        else:
            car_data[field] = value

    if issues:
        Logger.warn(f"Brak danych: \n{issues}")
        raise Exception("\n".join(issues))

    return add_car_data_fields(car_data)


def add_car_data_fields(car_data):
    register_date = datetime.strptime(car_data["firstRegistrationAt"], "%Y-%M-%d")
    car_data["firstRegistrationAt"] = register_date.strftime("%d.%M.%Y")

    filename = f'HISTORIA_{car_data["registrationNumber"]}.pdf'
    car_data["file_name"] = filename

    return car_data


def get_keeper_email(keeper):
    keeper_emails = excel_read.get_rows_from("ustawienia.xlsx", keeper_emails_settings)

    for email in keeper_emails:
        if email["keeper_name"] == keeper:
            return email["keeper_email"]

    return "Nie znaleziono w ustawienia.xlsx"


def main_task(api, sub_order, parent_order_id):
    keeper_email = ""
    keeper = ""

    try:
        parent_order_details = api.get_order_details(parent_order_id)
        keeper = parent_order_details["task"]["assignee"]["fullname"]

        keeper_email = get_keeper_email(keeper)
        car_data = get_required_fields(parent_order_details)

        CepikAPI().download_pdf(car_data)
        attachment_result = api.add_attachment(sub_order, car_data["file_name"])
        os.remove(car_data["file_name"])

        if "wczytane" in str(attachment_result):
            Logger.info(f"Historia dla {sub_order['number']} poprawnie dodana")
            return {"order_number": sub_order['number'], "result": "ok", "keeper": keeper}

        Logger.error(f"Historia dla {sub_order['number']} nie dodana! Blad:{attachment_result}")
        return {"order_number": sub_order['number'], "result": "error",
                "reason": f"Blad dodawania historii: {attachment_result}",
                "keeper_email": keeper_email, "keeper": keeper}

    except Exception as error:
        return {"order_number": sub_order['number'], "result": "error", "reason": str(error),
                "keeper_email": keeper_email, "keeper": keeper}


def send_report(report):
    subject_short_report = f"udanych:{report['successes_count']} bledow:{report['failures_count']}"
    subject = f"Raport robota cepik-historia {subject_short_report} "

    mail_sender.send_email(subject, report["report"], settings["target_emails"]["robot_email"], settings)


def send_reports(reports):
    for email, msg in reports.items():
        subject = f"Raport robota cepik-historia {datetime.now()}"

        mail_sender.send_email(subject, msg, email, settings)


def add_comment(api, result, order_id):
    if result["result"] == "ok":
        msg = f"Historia CEPIK - PDF został pomyślnie dodany!"
    else:
        msg = f"Historia CEPIK - błąd dodawania PDF\n"

        if "Brak wymaganego pola" in result["reason"]:
            msg += result["reason"]

    try:
        api.add_comment_to_order(order_id, msg)
    except Exception as error:
        Logger.error(traceback.format_exc())
        robot_manager.send_error(f"Blad glowny robota cepik-historia: {error}", settings, "cepik-historia")


def check_comments(api, order_id):
    comments = api.get_order_comments(order_id)
    return ZordonHelper.do_comments_contain(comments, "Historia CEPIK")


def filter_out_done(orders):
    filtered_orders = []

    for order in orders:
        if order['number'] in processed_orders:
            continue

        filtered_orders.append(order)

    return filtered_orders


def loop_task(api, orders):
    results = []

    try:
        for index, order in enumerate(orders):
            Logger.info(f"order_number: {order['number']} Progress: {index + 1}/{len(orders)}")

            processed_orders.append(order['number'])

            parent_order_id = order["parentId"]
            order_id = order["id"]

            if check_comments(api, order_id):
                Logger.info("Zlecenie zostalo już wczesniej sprawdzone")
                continue

            result = main_task(api, order, parent_order_id)
            Logger.info(result)
            results.append(result)
            add_comment(api, result, order_id)

        Logger.info(results)

        if results:
            report = get_robot_report(results)
            robot_manager.save_report(report["report"])
            send_report(report)
            send_reports(get_reports(results))

    except Exception as error:
        Logger.error(f"loop_task error: {error}")
        Logger.error(traceback.format_exc())
        robot_manager.send_error(f"Blad glowny robota cepik-historia: {error}", settings, "cepik-historia")


def get_orders(api):
    added_orders = []
    orders = []
    sent_orders = api.get_orders_by({"state": "Wysłane", "orderType": "kosztorys AUDATEX"})
    confirmed_orders = api.get_orders_by({"state": "Potwierdzone", "orderType": "kosztorys AUDATEX"})

    for order in sent_orders + confirmed_orders:
        if order["id"] not in added_orders:
            added_orders.append(order["id"])
            orders.append(order)

    filtered_orders = filter_out_done(orders)

    return filtered_orders


def loop():
    try:
        api = ZordonAPI(settings["zordon_data"])
        orders = get_orders(api)

        Logger.info(f"Znaleziono {len(orders)} zlecen")

        if not orders:
            return

        loop_task(api, orders)
    except Exception as error:
        Logger.error(f"loop error: {error}")
        Logger.error(traceback.format_exc())
        robot_manager.send_error(f"Blad robota cepik-historia: {error}", settings, "cepik-historia")


try:
    if robot_manager.avoid_robot_duplicate():
        Logger.error(f"Robot '{ntpath.basename(sys.executable)}' jest już uruchomiony! Sprawdz otwarte procesy.")
    else:
        settings = excel_read.read_cells("ustawienia.xlsx", cepik_history_settings)
        file_manager.directory_creator(["raporty"])
        processed_orders = []

        loop()
except Exception as main_error:
    Logger.error(main_error)
    Logger.error(traceback.format_exc())
