# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 15:47:45 2022

@author: Schmuck
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 12:52:21 2022

@author: isaactrussell
"""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests, os
import time, datetime, sys
import csv
import urllib.parse
import pandas as pd
import nltk
import numpy as np

import matplotlib.pyplot as plt

class OMSCS_Scraper:
    
    def __init__(self):
        self._baseURL = "https://omshub.org"
        if sys.platform == "win32":
            driverPath = os.getcwd() + "/chromedriver.exe"
        else:
            driverPath = os.getcwd() + "/chromedriver" 
        options = Options()
        options.headless = True
        self._availableClasses = self._GetAvailableClasses()
        self._driver = webdriver.Chrome(driverPath, options = options)
        
    def _GetAvailableClasses(self):
        with open(os.getcwd() + "/ClassList.csv", "r") as f:
            file = csv.reader(f)
            return {i[1]: i[0] for i in file}
    
    def GetClassData(self, classId):
        try:
            className = self._GetAvailableClasses()[classId]
        except KeyError:
            raise KeyError("Class {} Not In Available Class List".format(classId))
            
        print("Gathering Data for {} {}".format(classId, className))
        class_ = self._OMSCS_Class(classId, className)
        html = self.getClassHtml(class_)
        classData = self.ParseHtml(html)
        class_.CreateClassData(classData)
        return class_
           
    def getClassHtml(self, class_):
        encoded = urllib.parse.urlencode({"classid": class_.classId, "title": class_.className})
        url = self._baseURL + "/class/{}?".format(class_.classId) + encoded
        self._driver.get(url) 
        time.sleep(3)
        return self._driver.page_source
      
    def ParseHtml(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        divs = soup.find("div", class_ = "MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-3 css-1h77wgb")
        out = {}
        for n, div in enumerate(divs.find_all("div", class_ = "MuiGrid-root MuiGrid-item css-tolxbf")):
            ratings = div.find("div", class_ = "MuiBox-root css-1yp4ln")
            sentiment = div.find("article")
            date = div.find("div", class_ = "MuiBox-root css-i3pbo")
            temp = {}
            temp.update({"sentiment": sentiment.text, "date": datetime.datetime.strptime(date.text.split(' ')[-1], "%m/%d/%Y")})
            for i in ratings.find_all("div"):
                parse = i.text.split(" ")
                temp.update({parse[0]: float(parse[1])})
            out.update({n: temp})
        return out
    
    def End(self):
        self._driver.quit()
        
    
    class _OMSCS_Class:
        
        def __init__(self, classId, className):
            self.classId = classId
            self.className = className
            self.classData = None
        
        def __repr__(self):
            rows = {"Avg Workload": self.classData.avgWorkload, "Avg Rating": self.classData.avgRating, "Avg Difficulty": self.classData.avgDifficulty, "# of Reviews": self.classData.numReviews}
            max_len = max([len(i) for i in rows])
            dist_away = 5
            try:
                out = "{} {}\n".format(self.classId, self.className)
                out += "".join(["*" for _ in range(len(out) -1)]) + '\n'
                for i in rows:
                    out += i
                    if len(i) < max_len:
                        out += "".join([" " for _ in range(max_len - len(i))])
                    out += "".join([" " for _ in range(dist_away)])
                    if i != "# of Reviews":
                        out += "{:.2f}".format(rows[i])
                    else:
                        out += str(rows[i])
                    out += "\n"
            
                return out
            except:
                return "{} {}\n".format(self.classId, self.className)
        
        def GraphData(self):
            fig, ax = plt.subplots(3,1)
            fig.suptitle("{} {}".format(self.classId, self.className))
            alpha = 0.5
            roll_val = 30
            data = self.classData.dataFrame.sort_values("date", ascending = True)
            x = data["date"].values
            
            ax[0].set_title("Ratings")
            values = data["Rating"]
            rolling = values.rolling(roll_val).mean()
            ax[0].scatter(x, values.values, alpha = alpha)
            ax[0].plot(x, rolling.values)
            
            ax[1].set_title("Workload")
            values = data["Workload"]
            rolling = values.rolling(roll_val).mean()
            ax[1].scatter(x, values.values, alpha = alpha, color = "r")
            ax[1].plot(x, rolling.values, color = 'r')
            
            ax[2].set_title("Difficulty")
            values = data["Difficulty"]
            rolling = values.rolling(roll_val).mean()
            ax[2].scatter(x, values.values, alpha = alpha, color = 'g')
            ax[2].plot(x, rolling.values, color = "g")
        
        def CreateClassData(self, data):
            self.classData = self._ClassData(data, self.className)
            
        class _ClassData:
            
            def __init__(self, data_in, className):
                self._className = className
                self.rawData = data_in
                self.dataFrame = self._createDF(data_in)
                self._GenerateStats()
                short_name = "".join([i[0].lower() for i in className.split(" ")])
                self.sentiments = self._PreprocessSentiments(stop_words = [short_name, "omscs", "course", "class", "assignment", "assignments", "project"])
            
            def _createDF(self, data):
                df = pd.DataFrame.from_dict(data).transpose()
                return df
            
            def _GenerateStats(self):
                avgs = self.dataFrame[["Rating", "Workload", "Difficulty"]].mean()
                self.avgRating = avgs["Rating"]
                self.avgWorkload = avgs["Workload"]
                self.avgDifficulty = avgs["Difficulty"]
                self.numReviews = len(self.dataFrame)
                
            def _PreprocessSentiments(self, stop_words = None):
                stopwords = nltk.corpus.stopwords.words("english")
                stopwords.extend(nltk.tokenize.word_tokenize(self._className.lower()))
                if stop_words:
                    stopwords.extend([i.lower() for i in stop_words])
                output = {}
                for i in self.rawData:
                    tokens = nltk.tokenize.word_tokenize(self.rawData[i]["sentiment"])
                    tokens = [w for w in tokens if w.lower() not in stopwords]
                    tokens = [w.lower() for w in tokens if w.isalpha()]
                    output.update({i: tokens})
                return self._ClassSentiments(output)
            
            def commonWords(self, n):
                fd = nltk.FreqDist(self.sentiments.flat)
                dist = fd.most_common(n)
                words = []
                values = []
                for i in dist:
                    words.append(i[0].capitalize())
                    values.append(i[1])
                y_pos = np.arange(len(words))
                plt.barh(y_pos, values, align = "center", alpha = 0.5)
                plt.yticks(y_pos, words)
                plt.title("Common Words from Reviews for {}".format(self._className))
        
            class _ClassSentiments:
                
                def __init__(self, data):
                   self.raw = data
                   self.flat = self._flatten()
                
                def _flatten(self):
                    lol = [self.raw[i] for i in self.raw]
                    return [x for xs in lol for x in xs]
                
if __name__ == "__main__":
    
    Scrape = OMSCS_Scraper()
    class1 = Scrape.GetClassData("CS-7643")
    # class2 = Scrape.GetClassData("CS-6300")
    class1.classData.commonWords(20)
    # print(class2.classData.sentiments.flat)
    # class_.GraphData()
    
    Scrape.End()
