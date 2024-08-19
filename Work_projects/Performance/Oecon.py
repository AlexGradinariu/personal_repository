import time
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import optparse

parser = optparse.OptionParser()
parser.add_option('-n','--number',
    action="store",dest="number",help="the phone number", default=None)
options, args = parser.parse_args()

number=str(options.number)

if len(number) < 6:
    parser.error("Phone number NOK")


def open_browser():
    global browser
    browser = Chrome()
    browser.maximize_window()
    browser.implicitly_wait(10)


def login():
    browser.get("https://ecalldev03.comloc.net/login")
    name = browser.find_element(By.ID,value="user")
    name.send_keys("Alex.Gradinariu")
    password = browser.find_element(By.ID, value="password")
    password.send_keys("4321")
    browser.find_element(By.CSS_SELECTOR,value="button.btn").click()
    print("Login Done")


def check_call():
    browser.find_element(By.CSS_SELECTOR,value="ul.nav:nth-child(2) > li:nth-child(3) > a:nth-child(1)").click()
    wait = WebDriverWait(browser, 35)
    print(number)
    wait.until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'{}')]".format(number))))
    my_phone = browser.find_element(By.XPATH,("//*[contains(text(),'{}')]".format(number)))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".selected-row > td:nth-child(3) > span:nth-child(1)")))
    time.sleep(0.5)
    my_phone.click()
    print(my_phone.text)
    browser.find_element(By.XPATH,value="/html/body/div[2]/div[1]/div[1]/div[2]/div[3]/button").click()
    time.sleep(0.5)
    browser.find_element(By.CSS_SELECTOR,value="#s2id_phoneId").click()
    time.sleep(0.5)
    input = browser.find_element(By.ID,value="s2id_autogen2_search")
    input.send_keys("{}".format(number))
    body = browser.find_element(By.CSS_SELECTOR,value=".select2-results-dept-0").click()
    time.sleep(0.5)
    browser.find_element(By.ID,value="callIvsButton").click()
    time.sleep(2)
    browser.quit()
    print("Successfully callback")


if __name__ == "__main__":
    open_browser()
    login()
    check_call()