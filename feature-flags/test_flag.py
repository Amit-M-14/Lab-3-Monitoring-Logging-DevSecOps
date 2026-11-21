import sys
from selenium import webdriver
from selenium.webdriver.common.by import By

expected = sys.argv[1]
d = webdriver.Remote("http://localhost:4444", options=webdriver.ChromeOptions())
d.get("http://host.docker.internal:5060/")
actual = d.find_element(By.ID, "title").text
print("Expected:", expected, "| Actual:", actual)
print("PASS" if actual == expected else "FAIL")
d.quit()
