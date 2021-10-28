import urllib.parse as urlparse
from urllib.parse import urlencode

import requests
import urllib3
from bs4 import BeautifulSoup

from common.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CepikAPI:

    def __init__(self):
        self.session = requests.Session()

    def get_form_data(self):
        response = self.session.get("https://historiapojazdu.gov.pl/", verify=False)
        html = BeautifulSoup(response.text, features="lxml")
        form = html.select_one("form[id='_historiapojazduportlet_WAR_historiapojazduportlet_:formularz']")
        input_view_state = form.select_one("input[id='javax.faces.ViewState']")

        return {
            "url": form.attrs.get("action"),
            "view_state": input_view_state.attrs.get("value"),
        }

    def add_foreign_data(self, html, form_data, car_data):
        try:
            view_state_input = html.select_one("form[name*=carfax] input[id='javax.faces.ViewState']")
            view_state = view_state_input.attrs.get("value")

            url = "https://historiapojazdu.gov.pl/strona-glowna"

            query_params = {
                "p_p_id": "historiapojazduportlet_WAR_historiapojazduportlet",
                "p_p_lifecycle": "2",
                "p_p_state": "normal",
                "p_p_mode": "view",
                "p_p_cacheability": "cacheLevelPage",
                "p_p_col_id": "column-1",
                "p_p_col_count": "1",
                "_historiapojazduportlet_WAR_historiapojazduportlet__jsfBridgeAjax": "true",
                "_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdResource": "/views/view.xhtml",
                "_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdRender": "/views/index.xhtml",
                "_historiapojazduportlet_WAR_historiapojazduportlet_javax.faces.ViewState": form_data["view_state"],
                "_historiapojazduportlet_WAR_historiapojazduportlet_:vin": car_data["vin"],
                "_historiapojazduportlet_WAR_historiapojazduportlet_:data": car_data["firstRegistrationAt"],
                "_historiapojazduportlet_WAR_historiapojazduportlet_:btnSprawdz": "SprawdÅº pojazd Â»",
                "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz": "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz",
                "_historiapojazduportlet_WAR_historiapojazduportlet_:rej": car_data["registrationNumber"],
                "_historiapojazduportlet_WAR_historiapojazduportlet_javax.faces.encodedURL": "https://historiapojazdu.gov.pl/strona-glowna?p_p_id=historiapojazduportlet_WAR_historiapojazduportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1&_historiapojazduportlet_WAR_historiapojazduportlet__jsfBridgeAjax=true&_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdResource=%2Fviews%2Findex.xhtml"
            }

            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(query_params)

            url_parts[4] = urlencode(query)

            full_url = urlparse.urlunparse(url_parts)

            data = {
                "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form": "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form",
                f"javax.faces.encodedURL": f"https://historiapojazdu.gov.pl/strona-glowna?p_p_id=historiapojazduportlet_WAR_historiapojazduportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1&_historiapojazduportlet_WAR_historiapojazduportlet__jsfBridgeAjax=true&_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdResource=%2Fviews%2Fview.xhtml&_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdRender=%2Fviews%2Findex.xhtml&_historiapojazduportlet_WAR_historiapojazduportlet_javax.faces.ViewState={form_data['view_state']}&_historiapojazduportlet_WAR_historiapojazduportlet_:vin={car_data['vin']}&_historiapojazduportlet_WAR_historiapojazduportlet_:data={car_data['firstRegistrationAt']}&_historiapojazduportlet_WAR_historiapojazduportlet_:btnSprawdz=Sprawd%C3%85%C2%BA+pojazd+%C3%82%C2%BB&_historiapojazduportlet_WAR_historiapojazduportlet_:formularz=_historiapojazduportlet_WAR_historiapojazduportlet_%3Aformularz&_historiapojazduportlet_WAR_historiapojazduportlet_:rej={car_data['registrationNumber']}&_historiapojazduportlet_WAR_historiapojazduportlet_javax.faces.encodedURL=https%3A%2F%2Fhistoriapojazdu.gov.pl%2Fstrona-glowna%3Fp_p_id%3Dhistoriapojazduportlet_WAR_historiapojazduportlet%26p_p_lifecycle%3D2%26p_p_state%3Dnormal%26p_p_mode%3Dview%26p_p_cacheability%3DcacheLevelPage%26p_p_col_id%3Dcolumn-1%26p_p_col_count%3D1%26_historiapojazduportlet_WAR_historiapojazduportlet__jsfBridgeAjax%3Dtrue%26_historiapojazduportlet_WAR_historiapojazduportlet__facesViewIdResource%3D%252Fviews%252Findex.xhtml",
                "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:loadingMessageField": "Wyszukiwanie w zewnętrznej bazie danych...",
                "javax.faces.ViewState": view_state,
                "javax.faces.source": "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:napisPokazCar",
                "javax.faces.partial.event": "click",
                "javax.faces.partial.execute": "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:napisPokazCar _historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:napisPokazCar",
                "javax.faces.partial.render": "_historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:ryzykaPojazdGroup _historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:daneAutoDnaGroup _historiapojazduportlet_WAR_historiapojazduportlet_:pokaz-dane-carfax-form:komunikat",
                "javax.faces.behavior.event": "action",
                "javax.faces.partial.ajax": "true"
            }

            self.session.post(full_url, data=data, verify=False)

        except Exception as error:
            Logger.error(f"Blad dodawania danych zagranicznych: {error}")

    def get_pdf_url(self, car_data, form_data):
        data = {
            "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz": "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz",
            "_historiapojazduportlet_WAR_historiapojazduportlet_:rej": car_data["registrationNumber"],
            "_historiapojazduportlet_WAR_historiapojazduportlet_:vin": car_data["vin"],
            "_historiapojazduportlet_WAR_historiapojazduportlet_:data": car_data["firstRegistrationAt"],
            "_historiapojazduportlet_WAR_historiapojazduportlet_:btnSprawdz": "Sprawdź pojazd »",
            "javax.faces.ViewState": form_data["view_state"],
        }

        response = self.session.post(form_data["url"], data=data, verify=False)
        html = BeautifulSoup(response.text, features="lxml")
        download_button = html.select_one(".download-btn")

        if not download_button:
            raise Exception(f"Błąd pobierania historii PDF dla {car_data['registrationNumber']}")

        return download_button.attrs.get("href"), html

    def download_pdf(self, car_data):
        form_data = self.get_form_data()
        url, html = self.get_pdf_url(car_data, form_data)
        self.add_foreign_data(html, form_data, car_data)
        response = self.session.get(url, verify=False)

        with open(car_data['file_name'], "wb") as file:
            file.write(response.content)
