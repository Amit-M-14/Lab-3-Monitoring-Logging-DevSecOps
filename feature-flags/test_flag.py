import os, sys
from selenium import webdriver
from selenium.webdriver.common.by import By

expected = sys.argv[1]
url = os.environ.get("APP_URL", "http://flagapp:8080/")
d = webdriver.Remote("http://localhost:4444", options=webdriver.ChromeOptions())
try:
    d.get(url)
    els = d.find_elements(By.ID, "title")
    if not els:
        print("Page title:", d.title)
        print("FAIL (title element not found)")
    else:
        actual = els[0].text
        print("Expected:", expected, "| Actual:", actual)
        print("PASS" if actual == expected else "FAIL")
finally:
    d.quit()
