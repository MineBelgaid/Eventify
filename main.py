import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions


import yaml


def load_config(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(f"Error loading YAML file: {e}")
            return None


from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from src.scraping_strategies import ScraperContext, SeleniumStrategy, EndpointStrategy


def main() -> None:
    # Load configuration
    configs_path = "./src/config.yaml"
    configs = load_config(configs_path)
    if not configs:
        print("Failed to load configuration, exiting...")
        return

    # Setup Chrome WebDriver options
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    print(len(configs))


    results = []
    for item in configs.values():

        # Instantiate the ScraperContext with the loaded config
        # Pass the driver to the context if using selenium_strategy
        if item.get("strategy") == "selenium_strategy":
            item["driver"] = driver  # Add driver to config
        context = ScraperContext(item)

        start_urls = [{"url": item.get("base_url", "")}]

        for start_url_dict in start_urls:
            url = start_url_dict.get("url")
            print(f"Scraping {url} ...")
            try:
                # Execute scraping with strategy-specific configuration
                results += context.execute_scrape(item)
                print(f"Extracted {len(results)} items from {url}.")
                # TODO: Process the results as needed
            except Exception as e:
                print(f"Cannot extract data from {url}: {e}")
        # Clean up WebDriver
    driver.quit()
    # save the results to a file
    with open("results.json", "w") as file:
        json.dump(results, file, indent=4)    


if __name__ == "__main__": 
    main()
