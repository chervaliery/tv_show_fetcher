import requests
import pytesseract
import time
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display

from models import *
from django.conf import settings

def get_show():
    final_url = "{0}/{1}/profile".format(settings.USER_URL, settings.USER_ID)
    resp = requests.get(final_url, params=settings.USER_PARAMS).json()

    for show in resp["shows"]:
        print show
        id = show['id']
        try:
            s = Show.objects.get(tst_id=id)
        except Show.DoesNotExist:
            s = Show()
            s.tst_id = show['id']
            s.enabled = False
        s.name = show['name']
        s.save()

def fetch_show(show):
    final_url = "{0}/{1}/data/en".format(settings.SHOW_URL, show.tst_id)
    resp = requests.get(final_url, params=settings.SHOW_PARAMS).json()

    for episode in resp["episodes"]:
        id = episode['id']
        try:
            ep = Episode.objects.get(tst_id=id)
        except Episode.DoesNotExist:
            ep = Episode()
            ep.season = episode['season_number']
            ep.number = episode['number']
            ep.show = show
            ep.tst_id = episode['id']
            ep.downloaded = False
            ep.path = '/'

        ep.watched = episode['seen']
        ep.date = episode['air_date']
        ep.name = episode['name']
        if not episode['air_date']:
            ep.aired = False
        else:
            ep.aired = episode['aired']
        ep.save()

def download_episode(episode_list):
    resp = {}
    display = init_display(0, (1600, 900))
    driver = init_driver()
    for episode in episode_list:
        try:
            res = lookup(driver, str(episode), settings.PREFERD_RES)
        except NoSuchElementException:
            first_step(driver)
            time.sleep(5)
            while not driver.find_elements_by_xpath('//*[@id="searchinput"]'):
                captcha(driver)
                time.sleep(5)
            res = lookup(driver, str(episode), settings.PREFERD_RES)
        time.sleep(5)
        resp[episode] = res
    driver.quit()
    return resp

def init_display(visible, size):
    display = Display(visible=visible, size=size)
    display.start()
    return display

def init_driver():
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option("prefs", settings.CHROME_PREF)

    driver = webdriver.Chrome(chrome_options=chromeOptions)
    time.sleep(5)
    return driver

def first_step(driver):
    link = driver.find_element_by_xpath('/html/body/div/div/a')
    link.click()

def captcha(driver):
    #taking screenshot
    driver.save_screenshot(settings.CAPTCHA_PATH)

    #crop image
    image_element = driver.find_element_by_xpath('/html/body/form/div/div/table[1]/tbody/tr[2]/td[2]/img')
    location = image_element.location
    size = image_element.size
    crop_image(settings.CAPTCHA_PATH, location, size)

    #capture image text
    text = recover_text(settings.CAPTCHA_PATH).strip()

    inputElement = driver.find_element_by_xpath('//*[@id="solve_string"]')
    inputElement.send_keys(text)
    inputElement.send_keys(Keys.RETURN)

def crop_image(path, location,size):
    image = Image.open(path)
    x,y = int(location['x']), int(location['y'])
    w,h = int(size['width']), int(size['height'])
    image.crop((x, y, x+w, y+h)).save(path)

def recover_text(filename):
    image = Image.open(filename)
    r, g, b, a = image.split()
    image = Image.merge('RGB', (r, g, b))
    return pytesseract.image_to_string(image)

def lookup(driver, query, resolution):
    driver.get("https://rarbg.to/torrents.php")
    time.sleep(5)
    inputElement = driver.find_element_by_xpath('//*[@id="searchinput"]')
    inputElement.send_keys("{0} {1}".format(query, resolution))
    driver.find_element_by_xpath('//*[@id="searchTorrent"]/table/tbody/tr[1]/td[2]/button').click()
    time.sleep(1)
    try:
        driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td[2]/div/table/tbody/tr[2]/td/table[2]/tbody/tr[2]/td[2]/a[1]')
        driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td[2]/div/table/tbody/tr[2]/td/table[2]/tbody/tr[1]/td[5]/a').click()
        time.sleep(1)
        driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td[2]/div/table/tbody/tr[2]/td/table[2]/tbody/tr[2]/td[2]/a[1]').click()
    except NoSuchElementException:
        if resolution:
            return lookup(driver, query, '')
        else:
            return False
    time.sleep(1)
    driver.find_element_by_xpath('/html/body/table[3]/tbody/tr/td[2]/div/div/table/tbody/tr[2]/td/div/table/tbody/tr[1]/td[2]/a[1]').click()
    return True
