#!/usr/bin/python3

import requests
import urllib.request
from bs4 import BeautifulSoup
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'wordoftheday.txt')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'output.txt')
url = 'https://www.wordsmith.org/words/today.html'
keywords = ['USAGE:\n', 'MEANING:\n', 'PRONUNCIATION:\n', 'ETYMOLOGY:\n', 'NOTES:\n']
        
def readFile(path):
	with open(path, 'r') as f:
		return f.read()

def writeFile(content):
	with open(DEFAULT_PATH, 'w') as f:
		f.write(content)

def stripBlank():
	with open(DEFAULT_PATH) as f, open('output.txt', 'w') as outfile:
		for line in f:
			if line in keywords:
				line = '**'+line+'**'
			if not line.strip(): continue
			outfile.write(line)
		
def getWebPage():
	response = requests.get(url)
	soup = BeautifulSoup(response.text, "html.parser")

	pageText = soup.get_text()

	step1 = pageText.split('with Anu Garg')
	step2 = step1[1].split('A THOUGHT FOR TODAY')
	step3 = step2[0].strip()
	
	writeFile(step3)
	stripBlank()

def getTodaysWord(toUpdate):
	if toUpdate:
		print('UPDATING WORD OF THE DAY')
		getWebPage()
	banner = readFile(OUTPUT_FILE)
	return banner
