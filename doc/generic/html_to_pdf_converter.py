# python-selenium-chrome-html-to-pdf-converter
# Simple python wrapper to convert HTML to PDF with headless Chrome via selenium.
# https://github.com/maxvst/python-selenium-chrome-html-to-pdf-converter
# MIT License

import sys, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json, base64

def send_devtools(driver, cmd, params={}):
  resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
  url = driver.command_executor._url + resource
  body = json.dumps({'cmd': cmd, 'params': params})
  response = driver.command_executor._request('POST', url, body)
  if response.get('status'):
    raise Exception(response.get('value'))
  return response.get('value')

def get_pdf_from_html(path, print_options = {}):
  webdriver_options = Options()
  webdriver_options.add_argument('--no-sandbox')
  webdriver_options.add_argument('--headless')
  webdriver_options.add_argument('--disable-gpu')

  # running on windows
  if os.name == 'nt': 
    # append C:/ to path
    path = 'C:/' + path
    # look for chromedriver at /home/chromedriver/chromedriver 
    driver = webdriver.Chrome('/home/chromedriver/chromedriver', options=webdriver_options)
  else:
    # running on linux
    path = 'file://' + path
    driver = webdriver.Chrome(options=webdriver_options)

  driver.get(path)

  calculated_print_options = {
    'landscape': False,
    'displayHeaderFooter': False,
    'printBackground': True,
	  'preferCSSPageSize': True,
  }
  calculated_print_options.update(print_options)
  result = send_devtools(driver, "Page.printToPDF", calculated_print_options)
  driver.quit()
  return base64.b64decode(result['data'])
