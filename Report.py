# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 22:31:23 2022

@author: Schmuck
"""

from Scraper import OMSCS_Scraper

class OMSCS_ClassReport:
    
    def __init__(self, classId):
        scraper = OMSCS_Scraper()
        self.class_ = scraper.GetClassData(classId)
        scraper.End()
        
    def Generate(self):
        print("Report Generation!")
        
if __name__ == "__main__":
    report = OMSCS_ClassReport("CS-7638").Generate()