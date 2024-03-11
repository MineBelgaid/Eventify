import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class ScraperContext:
    def __init__(self, config):
        self.strategy = self._select_strategy(config)

    def _select_strategy(self, config):
        base_url = config.get("base_url")
        if config.get("strategy") == "selenium_strategy":
            driver = config.get("driver")
            return SeleniumStrategy(driver, base_url)
        elif config.get("strategy") == "endpoint_strategy":
            return EndpointStrategy(base_url)
        elif config.get("strategy") == "requests_strategy":
            return RequestsStrategy(base_url)
        else:
            raise ValueError(f"Unsupported strategy: {config.get('strategy')}")

    def execute_scrape(self, config):
        return self.strategy.scrape(config["config"])


class ScrapingStrategy(ABC):
    @abstractmethod
    def scrape(self, config):
        pass


class SeleniumStrategy(ScrapingStrategy):
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url

    def scrape(self, config):
        self.driver.get(self.base_url)
        visibility = config.get("visible", True)
        print(visibility)
        scroll = config.get("scroll", False)
        if scroll:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
        if visibility:
            WebDriverWait(self.driver, 200).until(
                EC.visibility_of_element_located((By.XPATH, config["wait_for"]))
            )
        else:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, config["wait_for"]))
            )

        containers = self.driver.find_elements(By.XPATH, config["container_selector"])
        print(len(containers))
        results = []

        for container in containers:
            item = {}
            for field, details in config["fields"].items():
                try:
                    if "attribute" in details:
                        element = container.find_element(By.XPATH, details["selector"])
                        value = element.get_attribute(details["attribute"])
                        if "urljoin" in details and details["urljoin"]:
                            value = urljoin(self.base_url, value)
                    else:
                        element = container.find_element(By.XPATH, details["selector"])
                        value = element.text.replace("\n", " ").strip()
                        print(value)
                        if field == "dateTime" and "format" in details:
                            temp = value
                            try:
                                if "regex" in details:
                                    value = re.search(details["regex"], value).group(0)
                                print(value)
                                print(details["format"])
                                print(datetime.strptime(value, details["format"]))
                            # Convert the dateTime using the specified format
                                value = datetime.strptime(
                                    value, details["format"]
                                ).strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                value = temp
                    print(value)
                    item[field] = value
                except:
                    if "default" in details:
                        item[field] = details["default"]
                    else:
                        # Skip this field if it's not found and doesn't have a default value
                        continue

            if item:  # Add item if not empty
                results.append(item)
        return results


class RequestsStrategy(ScrapingStrategy):
    def __init__(self, base_url):
        self.base_url = base_url

    def scrape(self, config):
        # Send a GET request to the URL
        response = requests.get(self.base_url)
        print("here")
        # Check if the request was successful
        if response.status_code != 200:
            return []

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Initialize results list to store data
        results = []

        # Extract data based on provided config
        containers = soup.select(config["container_selector"])
        print(len(container))
        for container in containers:
            item = {}
            for field, details in config["fields"].items():
                try:
                    if "attribute" in details:
                        element = container.select_one(details["selector"])
                        value = element[details["attribute"]] if element else None
                        if value and "urljoin" in details and details["urljoin"]:
                            value = urljoin(self.base_url, value)
                    else:
                        element = container.select_one(details["selector"])
                        value = element.text.strip() if element else None
                    if value:
                        item[field] = value
                except Exception as e:
                    print(f"Error extracting field {field}: {e}")
                    if "default" in details:
                        item[field] = details["default"]
                    else:
                        continue

            if item:  # Add item if not empty
                results.append(item)

        return results


class EndpointStrategy(ScrapingStrategy):
    def __init__(self, base_url):
        self.base_url = base_url

    def scrape(self, config):
        # Implementation for direct endpoint calls
        pass
