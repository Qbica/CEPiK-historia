import json
import uuid

import requests

from common.api.zordon.zordon_helper import ZordonHelper
from common.logger import Logger


class ZordonAPI:

    def __init__(self, data):
        self.base_url = data["url"]
        self.session = requests.Session()
        self.log_in(data["username"], data["password"])

    def log_in(self, username, password):
        url = f"{self.base_url}/core/security/check-login"
        data = {
            "username": username,
            "password": password,
        }

        Logger.info(f"url: {url}")

        response = self.session.post(url, data=data)

        Logger.info(f"log_in response.status_code: {response.status_code}")
        self.session.headers = {"Authorization": f"Bearer {response.json()['token']}"}

    def get_orders_by(self, filters):
        orders_per_page = 100
        start = 0
        orders = []

        while 1:
            params = {
                "format": "datatables",
                "draw": "3",
                "order[0][column]": "3",
                "order[0][dir]": "desc",
                "start": start,
                "length": orders_per_page,
                "search[value]": json.dumps(filters),
                "search[regex]": "false",
                "name": "grid_task_all",
            }

            url = f"{self.base_url}/intgen/all-tasks/vehicle"

            Logger.info(f"start: {start}")
            Logger.info(f"url: {url}")

            response = self.session.get(url, params=params)

            Logger.info(f"get_orders_by response.status_code: {response.status_code}")

            response_json = response.json()

            orders += response_json["data"]

            if len(response_json["data"]) < orders_per_page:
                break

            start += orders_per_page

        return orders

    def add_comment_to_order(self, order_id, comment):
        # internal_url = f"{self.base_url}/intgen/tasks/{order_id}/main/comments/internal"
        url = f"{self.base_url}/intgen/tasks/{order_id}/main/comments/public"

        if "test" in self.base_url:
            url = f"{self.base_url}/intgen/tasks/{order_id}/appraisal/comments/public"

        payload = {
            "type": 4,
            "content": comment,
        }

        Logger.info(f"url: {url}")
        Logger.info(f"payload: {payload}")

        response = self.session.post(url, json=payload)

        Logger.info(f"add_comment_to_order response.status_code: {response.status_code}")

        if "success" not in str(response.text):
            raise Exception(f"Nie udalo sie dodac komentarza do zlecenia:{order_id} blad:{response.text}")

    def add_attachment(self, order, file_name):
        url = f"{self.base_url}/storage/upload/intgen"

        files = {
            "file[0]": (f"{uuid.uuid4()}_{file_name}", open(file_name, "rb")),
        }

        data = {
            "path": ZordonHelper.get_upload_path(order),
        }

        Logger.info(f"url: {url}")
        Logger.info(f"files: {files}")

        response = self.session.post(url, data=data, files=files)

        Logger.info(f"add_attachment response.status_code: {response.status_code}")

        return response.text

    def get_order_comments(self, order_id):
        url = f"{self.base_url}/intgen/tasks/{order_id}/main/comments/public"

        Logger.info(f"url: {url}")

        response = self.session.get(url)

        return response.json()

    def get_order_details(self, order_id):
        url = f"{self.base_url}/intgen/tasks/main-vehicle/{order_id}"
        Logger.info(f"url: {url}")
        response = self.session.get(url)
        Logger.info(f"get_order_details response.status_code: {response.status_code}")

        return response.json()
