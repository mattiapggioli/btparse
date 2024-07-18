import csv
import re
from typing import *

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BTParser:
    url = "https://www.borsaitaliana.it/borsa/obbligazioni/mot/btp/lista.html"

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def quit(self):
        self.driver.quit()

    def find_element(
        self,
        by: str,
        value: str,
        wait: int = 10,
        over_element: Optional[WebElement] = None,
    ) -> Optional[WebElement]:
        if over_element is None:
            try:
                return WebDriverWait(self.driver, wait).until(
                    EC.presence_of_element_located((by, value))
                )
            except TimeoutException:
                return
        return over_element.find_element(by, value)

    def find_elements(
        self,
        by: str,
        value: str,
        wait: int = 10,
        over_element: Optional[List[WebElement]] = None,
    ) -> List[WebElement]:
        if over_element is None:
            try:
                return WebDriverWait(self.driver, wait).until(
                    EC.presence_of_all_elements_located((by, value))
                )
            except TimeoutException:
                return []
        return over_element.find_elements(by, value)

    def parse_btp(self, btp_element: WebElement) -> Dict[str, any]:
        btp = {}
        divs = self.find_elements(
            By.CSS_SELECTOR, "div.l-box", over_element=btp_element
        )
        isin_element = self.find_element(
            By.CSS_SELECTOR, "a", over_element=divs[0]
        )
        # * ISIN
        # Code
        btp["isin"] = (
            self.find_element(
                By.CSS_SELECTOR, "span.t-text", over_element=isin_element
            )
            .get_attribute("textContent")
            .replace(" -", "")
            .strip()
        )
        # Url
        btp["isin_url"] = isin_element.get_attribute("href").split("?")[0]
        # * Descrizione
        btp["descrizione"] = (
            self.find_element(
                By.CSS_SELECTOR, "span.t-text.-normal", over_element=divs[0]
            )
            .get_attribute("textContent")
            .strip()
        )
        text_in_div1 = " ".join(
            " ".join(divs[1].get_attribute("textContent").split()).split()
        )
        # 'Ultimo: 109,15 Cedola: 3,625 Scadenza: 01/11/2026'
        regex_by_key = [
            {"key": "cedola", "regex": r"Cedola: ([\d,]+)", "float": True},
            {"key": "ultimo", "regex": r"Ultimo: ([\d,]+)", "float": True},
            {
                "key": "scadenza",
                "regex": r"Scadenza: (\d+/\d+/\d+)",
                "float": False,
            },
        ]
        for rbk in regex_by_key:
            match = re.search(rbk["regex"], text_in_div1)
            if match is None:
                btp[rbk["key"]] = None
                continue
            if rbk["float"]:
                btp[rbk["key"]] = float(match.group(1).replace(",", "."))
                continue
            btp[rbk["key"]] = match.group(1)
        return btp

    def parse(self, page: int = 0) -> List[Dict[str, any]]:
        self.driver.get(f"{self.url}?page={page}")
        data = []
        btps = self.find_elements(By.CSS_SELECTOR, "article.u-hidden.-sm.-md")
        for btp in btps:
            data.append(self.parse_btp(btp))
        next_page_button = self.find_element(
            By.CSS_SELECTOR, "span.m-icon.-pagination-right"
        )
        if next_page_button:
            data += self.parse(page + 1)
        return data


if __name__ == "__main__":
    btparser = BTParser()
    data = btparser.parse()
    with open("data.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    btparser.quit()
