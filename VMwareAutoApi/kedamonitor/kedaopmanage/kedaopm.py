# encoding: utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def getalertinfo(opurl, opusername, oppassword):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--proxy-server=http://10.8.2.2:3128')
    browser = webdriver.Chrome(options=chrome_options)
    #print(dir(browser))

    browser.get("http://10.2.2.33:8086/Logout.do")

    def is_element_exist(css):
        s = browser.find_elements_by_id(css)
        if len(s) == 0:
            print("元素未找到:%s" %css) 
            return False
        elif len(s) == 1:
            return True
        else:
            print("找到%s个元素：%s" %(len(s),css))
            return False

    Username = browser.find_element_by_name('userName')
    # 填写前先清空
    Username.clear()
    # 模拟系统按键
    Username.send_keys(opusername)

    Password = browser.find_element_by_name('password')
    Password.clear()
    Password.send_keys(oppassword)

    jSubmit = browser.find_element_by_id('btnSubmit')
    # 模拟点击登录按钮
    jSubmit.click()
    browser.get(opurl)
    xpath = "//table[@class='tableFillBorder']/tbody/tr"
    tr_num = browser.find_elements_by_xpath(xpath)
    i = 2
    devicedict = dict()
    devicelist = list()
    while len(tr_num) > i:
        i = i + 1
        devname = browser.find_element_by_xpath("//table[@class='tableFillBorder']/tbody/tr[%s]/td[3]/a" %i)
        devalert = browser.find_element_by_xpath("//table[@class='tableFillBorder']/tbody/tr[%s]/td[4]/a" %i)    
        devaltime = browser.find_element_by_xpath("//table[@class='tableFillBorder']/tbody/tr[%s]/td[10]" %i)
        devstatu = browser.find_element_by_xpath("//table[@class='tableFillBorder']/tbody/tr[%s]/td[@class='rowOdd'][6] | //table[@class='tableFillBorder']/tbody/tr[%s]/td[@class='rowEven'][6]" %(i,i))
        devicedict['hostname'] = devname.text
        devicedict['alertinfo'] = devalert.text
        devicedict['alertstatus'] = devstatu.text
        devicedict['alerttime'] = devaltime.text
        devicelist.append(devicedict.copy())
    browser.close()
    return devicelist

