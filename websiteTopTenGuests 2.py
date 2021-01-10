from bs4 import BeautifulSoup
import requests
import unittest


url='https://www.esquire.com/uk/culture/g32032195/best-joe-rogan-episodes/'
page = requests.get(url)
names=[]
soup = BeautifulSoup(page.content, 'html.parser')

#gets all of the names of top 10 podcasts
temp = soup.find_all('span',class_="listicle-slide-hed-text")
for x in temp:
    names.append(x.string)
   
#print names of best podcast guests and the youtube links 
print(names)

