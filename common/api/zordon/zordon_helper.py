from datetime import datetime


class ZordonHelper:

    @staticmethod
    def get_main_order(orders):
        for order in orders:
            if "-" not in order["number"]:
                return order

        raise Exception("Nie znaleziono zlecenia glownego")

    @staticmethod
    def get_upload_path(order):
        created_at = datetime.strptime(order["createdAt"], "%Y-%m-%d %H:%M:%S")
        path_string = created_at.strftime("%Y%m")

        return f"{path_string}/{order['number'].replace('/', '_')}"

    @staticmethod
    def do_comments_contain(comments, string_to_check):
        for comment in comments:
            if string_to_check in comment["content"]:
                return True

        return False

    @staticmethod
    def get_main_orders(orders):
        return [order for order in orders if "-" not in order["number"]]
