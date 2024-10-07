from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import pandas as pd
import requests
from datetime import datetime
import csv

#Here we create a dictionary where the "key" is the name of the metric, and the values r all j empty rn
metricNames = {"Stock":[],"Price":[],"Target Price":[],"Median %":[], "Outperform":[],
               "Analyst BHS":[],"Analyst Rating":[],"Technicals(1 Month)":[],
               "PE Ratio Individual - Industry Average":[], "PEG Ratio Individual - Industry Average":[], 
               "ROA Individual - Industry Average":[],"ROE Individual - Industry Average":[],
               "ROI Individual - Industry Average":[],"P/B Individual - Industry Average":[],
               "D/E Individual - Industry Average":[],"External %":[],"EV/EBITDA":[],"Dividend %":[], 
               "AIG Score":[],"Momentum":[],"Next Earnings":[],"Range 52W":[],"Cap":[],"Industry":[],"Date":[]}
metricDf = pd.DataFrame(metricNames)

def getMetrics(tickers):
    global metricDf
    for ticker in tickers:
        # Call the other methods to gather data
        cnnMetrics = getCNNMetrics(ticker)
        guruMetrics = getGuruMasterMetrics(ticker)
        yahooMetrics = getYahooMetrics(ticker)
        finVizMetrics = getFinVizMetrics(ticker)
        zacksMetrics = getZacksMetrics(ticker)
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Fill up the dictionary with data
        newMetrics = {
            "Stock": ticker,
            "Price": cnnMetrics[2],
            "Target Price": cnnMetrics[3],
            "Median %": cnnMetrics[4], 
            "Outperform": cnnMetrics[0],
            "Analyst BHS": cnnMetrics[1],
            "Analyst Rating": "No clue what to put here",
            "Technicals(1 Month)": "Manually Input from Trading View",
            "PE Ratio Individual - Industry Average": f"{finVizMetrics['P/E']} - {zacksMetrics['PE (F1)']}", 
            "PEG Ratio Individual - Industry Average": f"{finVizMetrics['PEG']} - {zacksMetrics['PEG (Ratio)']}", 
            "ROA Individual - Industry Average": f"{finVizMetrics['ROA']} - {zacksMetrics['ROA']}",
            "ROE Individual - Industry Average": f"{finVizMetrics['ROE']} - {zacksMetrics['ROE']}",
            "ROI Individual - Industry Average": f"{finVizMetrics['ROI']} - {zacksMetrics['ROI']}",
            "P/B Individual - Industry Average": f"{finVizMetrics['P/B']} - {zacksMetrics['Price to Book']}",
            "D/E Individual - Industry Average": f"{finVizMetrics['Debt/Eq']} - {zacksMetrics['Debt-to-Equity']}",
            "External %": guruMetrics,
            "EV/EBITDA": yahooMetrics[0],
            "Dividend %": finVizMetrics["Dividend TTM"], 
            "AIG Score": "Needed to be calculated",
            "Momentum": finVizMetrics["Perf Year"],
            "Next Earnings": yahooMetrics[1],
            "Range 52W": cnnMetrics[7],
            "Cap": cnnMetrics[5],
            "Industry": cnnMetrics[6],
            "Date": date
        }
        newMetricsDf = pd.DataFrame([newMetrics])
        metricDf = pd.concat([metricDf, newMetricsDf], ignore_index=True)
    
    # Save to CSV file after processing all tickers
    with open('metrics.csv', 'w', newline='') as file:
        metricDf.to_csv(file, index=False)



def getCNNMetrics(ticker):
    print(ticker)
    #okay so we are using selenium, which basically simulates a web user. we use this to open up webpages 
    # and then we scrape data from the webpages using beautifulSoup4, which looks at the
    #html in the code and looks for the certain elements we want
    
    #this is just some setup
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Chrome/127.0.6533.73"
    )
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    serviceC = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=serviceC,options=chrome_options)
    
    #cnn
    cnnURL = f"https://www.cnn.com/markets/stocks/{ticker}"
    driver.get(cnnURL)
    
    #let page load
    time.sleep(2)
    
    #scroll full page
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #Parse CNN html
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    #so now this soup variable has all the html

    #check if ticker is found on CNN
    if soup.find('h1',attrs={'class':"error_headline"}):
        return ["CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker","CNN doesn't have this ticker"]

    #bhs
    # so here, when i looked through the html, I noticed that the buy hold sell graphic used the html keywords "markets-donut-chart"
    #and soem other unique stuff to identify it, so i call soup.find to look for those variables
    cnnBuy = soup.find('span', attrs={"class":"markets-donut-chart__legend--key-value","id":"markets-donut-chart__legend--key-value-buy"}).text
    cnnHold = soup.find('span', attrs={"class":"markets-donut-chart__legend--key-value","id":"markets-donut-chart__legend--key-value-hold"}).text
    cnnSell = soup.find('span', attrs={"class":"markets-donut-chart__legend--key-value","id":"markets-donut-chart__legend--key-value-sell"}).text
    bhs = cnnBuy+" "+cnnHold+" "+cnnSell


    #now imma do it for the rest of the elements 

    #price
    price = soup.find('div', attrs={'class':'price-2kQQGw cnn-pcl-eltrz4'}).text.strip()

    #target price
    targetPrice = soup.find_all('tspan',attrs={"fill":"#0C0C0C","font-family":"cnn_sans_display","font-size":"14px","font-weight":"500","text-anchor":"end","x":"0","y":"16"})[1].text.strip()
    
    #median percent
    percentList = soup.find_all('tspan',attrs={"fill":True,"font-family":"cnn_sans_display","font-size":"14px","font-weight":"500","text-anchor":"end","x":"-14","y":"32"})
    medianPercent = "??"
    if percentList[1]['fill'] == "#D50000":
        medianPercent = "-" + percentList[1].text.strip()
    elif percentList[1]['fill'] == "#008561":
        medianPercent = "+" + percentList[1].text.strip()

    #cap    
    insights = soup.find_all('span',attrs={'class':'markets-insights-list__item--title'})
    for insight in insights:
        if insight.text.strip()[:11] == "Market cap:":
            marketCap = insight.text.strip()[12:]

    #industry and dividend
    keyFacts = soup.find_all('div',attrs={'class':'markets-keyfacts__value-3a2Zj8 cnn-pcl-bn5xbk'})
    industry = (keyFacts[1].text.strip())
    

    #range
    ranges = soup.find_all('div',attrs={'class':'range-values cnn-pcl-ntwcbl'})[1]
    low = ranges.find('span', attrs={'class':'low__text'}).text.strip()
    high = ranges.find('span', attrs={'class':'high__text'}).text.strip()
    range = low + " - " + high

    #iframe to get outperform
    iframe_src = f"https://widgets.tipranks.com/content/v2/cnn/smartscoresmall/index.html?ticker={ticker}"
    driver.get(iframe_src)
    time.sleep(2)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    #outperform
    outperform = soup.find('text',attrs={"class":"sc-dnaUSb flXkAg"}).text

    #metrics. so now we take all the cnn metrics and put it in a array
    cnnMetrics = [outperform,bhs,price,targetPrice,medianPercent,marketCap,industry,range]
    return cnnMetrics

def getFinVizMetrics(ticker):
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Chrome/127.0.6533.73"
    )
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    serviceC = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=serviceC,options=chrome_options)
    
    #finviz
    finvizURL = f"https://finviz.com/quote.ashx?t={ticker}"
    driver.get(finvizURL)
    
    #let page load
    time.sleep(2)
    
    #scroll full page
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #Parse Finviz html
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    #check if ticker exists
    if soup.find('p',attrs={'class':"font-sans text-base leading-5 mt-6"}):
        return {"P/E":"FinViz doesn't have this ticker","ROE":"FinViz doesn't have this ticker","ROA":"FinViz doesn't have this ticker","ROI":"FinViz doesn't have this ticker","PEG":"FinViz doesn't have this ticker","P/B":"FinViz doesn't have this ticker","Debt/Eq":"FinViz doesn't have this ticker","Dividend TTM":"FinViz doesn't have this ticker","Perf Year":"FinViz doesn't have this ticker"}


    finVizDataRaw = soup.find_all('td', {
    'align': 'left',
    'class': 'snapshot-td2 w-[8%]',
    'style': ''})

    finVizDataCategories = soup.find_all('td', {
    'align': 'left',
    'class': 'snapshot-td2 cursor-pointer w-[7%]'})
    
    finVizDataClean = {}

    for (rawData,categories) in zip(finVizDataRaw,finVizDataCategories):
       if(not rawData.find('b')):
           break
       cleanData = rawData.find('b').text.strip()
       category = categories.text.strip()
       finVizDataClean[category] = cleanData

    keepKey = {"P/E" , "PEG" , "P/B" , "Debt/Eq" , "ROE" , "ROA" , "ROI","Dividend TTM","Perf Year"}
    finVizFinal = {key: finVizDataClean[key] for key in finVizDataClean if key in keepKey}
    start_index = finVizFinal["Dividend TTM"].find('(') + 1
    end_index = finVizFinal["Dividend TTM"].find(')')
    finVizFinal["Dividend TTM"] = finVizFinal["Dividend TTM"][start_index:end_index]
    if finVizFinal["Perf Year"] == "-":
        finVizFinal["Perf Year"] = "UNKNOWN-Check Manually"
    elif float(finVizFinal["Perf Year"].strip('%')) > 0:
        finVizFinal["Perf Year"] = "UP"
    elif float(finVizFinal["Perf Year"].strip('%')) < 0:
        finVizFinal["Perf Year"] = "DOWN"
    else:
        finVizFinal["Perf Year"] = "NEUTRAL"
    return finVizFinal


def getZacksMetrics(ticker):
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Chrome/127.0.6533.73"
    )
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    serviceC = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=serviceC,options=chrome_options)
    
    #zacks
    zacksURL = f"https://www.zacks.com/stock/quote/{ticker}"
    driver.get(zacksURL)
    
    #let page load
    time.sleep(2)
    
    #scroll full page
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #Parse zacks html
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    if not soup.find('a',attrs={'href':f'/stock/quote/{ticker}'}):
        return {"PE (F1)":"Zacks doesn't have this ticker","PEG (Ratio)":"Zacks doesn't have this ticker","Price to Book":"Zacks doesn't have this ticker","Debt-to-Equity":"Zacks doesn't have this ticker","ROE":"Zacks doesn't have this ticker","ROA":"Zacks doesn't have this ticker","ROI":"Zacks doesn't have this ticker"}
    
    industryLink = "https://www.zacks.com"+soup.find('a',{'class':'sector'}).get('href')
    #go to new industry page
    driver.get(industryLink)
    time.sleep(2)
    #scroll full page
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    #get new html
    html = driver.page_source
    soup = BeautifulSoup(html,"html.parser")
    rows = soup.find_all("tr")
    zacksMetrics = {}
    zMetricsKeep = {"PE (F1)","PEG (Ratio)","Price to Book","Debt-to-Equity","ROE","ROA","ROI"}
    for row in rows:
        columns = row.find_all("td")
        if len(columns) > 1:
            metric_name = columns[0].get_text(strip=True)
            if metric_name in zMetricsKeep:
                metric_value = columns[1].get_text(strip=True)
                zacksMetrics[metric_name] = metric_value
    zacksMetrics["ROE"] = zacksMetrics["ROE"]+"%"
    zacksMetrics["ROI"] = zacksMetrics["ROI"]+"%"
    zacksMetrics["ROA"] = zacksMetrics["ROA"]+"%"
    return zacksMetrics

def getGuruMasterMetrics(ticker):
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Chrome/127.0.6533.73"
    )
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    serviceC = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=serviceC,options=chrome_options)
    
    #guru
    guruURL = f"https://www.gurufocus.com/stock/{ticker}/summary"
    driver.get(guruURL)
    
    #let page load
    time.sleep(2)
    
    #scroll full page
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #Parse guru html
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    if soup.find('h1', class_='text-center m-b-md', string=f"Results similar to '{ticker}'"):
        return "GuruFocus does not have ticker"


    guruExternal = soup.find('span',{'class':'t-primary','data-v-0ed0d6db': True}).text.strip()
    return guruExternal

def getYahooMetrics(ticker):
    #using requests here
    yahooURL = f"http://finance.yahoo.com/quote/{ticker}/key-statistics"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(yahooURL, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
    ev_ebitda_row = soup.find('td', string='Enterprise Value/EBITDA').find_parent('tr')
    ev_ebitda_value = ev_ebitda_row.find_all('td')[1].text.strip()
    if ev_ebitda_value == "--":
        ev_ebitda_valueConv = "--"
    else:
        ev_ebitda_valueConv = (100-float(ev_ebitda_value))/100
    
    yahooURL = f"http://finance.yahoo.com/quote/{ticker}/analysis"
    response = requests.get(yahooURL, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
    if not soup.find('section',attrs={'data-testid':"earningsEstimate"}):
        return [ev_ebitda_valueConv,"Yahoo Doesn't Have This"]
    section = soup.find('section',attrs={'data-testid':"earningsEstimate"})
    body = section.find('tbody')
    rows = body.find_all('tr',attrs={'class':'yf-17yshpm'})
    row = rows[1]
    estimates = row.find_all('td',attrs={'class':'yf-17yshpm'})
    nextEarnings = estimates[1].text.strip()
    return [ev_ebitda_valueConv,nextEarnings]

listTick = ["FRT", "WBA", "MHK", "TPR","GNRC","HAS","MOS","LW","HSIC","MKTX","DAY","GL","WYNN","FMC","BBWI","IVZ","BWA","AAL","ETSY","CSCO","DHR","ABT","WFC","INTU","PM","AXP","IBM","AMGN","VZ","ISRG","CAT","RL","SOLV","LKQ","SJM","PODD"]
getMetrics(listTick)