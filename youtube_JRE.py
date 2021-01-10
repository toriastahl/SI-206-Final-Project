import re
import os
import numpy as np
import sqlite3
# import youtube_dl
# from tabulate import tabulate
import csv
import pandas
import unittest
import matplotlib
from textwrap import wrap
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter

#set up database
def readDataFromFile(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    f = open(full_path, encoding='utf-8')
    file_data = f.read()
    f.close()
    return file_data

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

# #below is all the functions to pull data from youtube (when the videos use to exist...)
# def getData():
#     ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})

#     with ydl:
#         ydl.params.update(ignoreerrors=True) #Dom Irrera's podcast is blocked on Copyright grounds
#         result = ydl.extract_info(
#             'https://www.youtube.com/playlist?list=UUzQUP1qoWDoEbmsQxvdjxgQ',
#             download = False # We just want to extract the info
#         )
#     id = []
#     titles = []
#     views = []
#     likes = []
#     dislikes = []
#     avg_rating = []
#     guest_names = []
#     for t in range(len(result['entries'])):
#         try:
#             id.append(result['entries'][t]['id'])
#             titles.append(result['entries'][t]['title'])
#             views.append(result['entries'][t]['view_count'])
#             likes.append(result['entries'][t]['like_count'])
#             dislikes.append(result['entries'][t]['dislike_count'])
#             avg_rating.append(result['entries'][t]['average_rating'])
#         except:
#             pass
#     dir = os.path.dirname('youtube_data.csv')
#     out_file = open(os.path.join(dir, 'youtube_data.csv'), "w")

#     #get guest names from titles
#     regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
#     pattern = re.compile(regex)
#     #go through each title and use refex to get name
#     for title in titles:
#         try:
#             guests = re.split(',|&', pattern.match(title).group('name'))
#             for person in guests:
#                 guest_names.append(person.strip()) 
#         except:
#             guest_names.append('N/A')
#     #write data to csv file
#     with open('youtube_data.csv') as f:
#         csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
#         csv_writer.writerow(["id","video_id","title","view","likes","dislikes","rating","guestid"])
#         for x in range(len(titles)):
#             try:
#                 cur.execute('SELECT id FROM JRP_guest_count WHERE name = ?',(guest_names[x], ))
#                 guestid = cur.fetchone()[0]
#             except:
#                 guestid=-1
#             csv_writer.writerow([id[x],titles[x],views[x],likes[x],dislikes[x],avg_rating[x],guestid])
#     out_file.close()

#function to put 25 items from csv file to database
def uploadDataJRE(cur,conn):
    cur.execute('''CREATE TABLE IF NOT EXISTS JRP (id INTEGER UNIQUE, video_id TEXT, title TEXT, views INTEGER, likes INTEGER, dislikes INTEGER, rating REAL, guestid INTEGER)''')
    # Pick up where we left off
    start = None
    #select max id (last one put in db)
    cur.execute('SELECT id FROM JRP WHERE id = (SELECT MAX(id) FROM JRP)')
    start = cur.fetchone()
    if (start!=None):
        start = start[0] + 1
    else:
        start = 1
    #open file to read data
    with open('youtube_data.csv','r') as f:
        csvreader = csv.reader(f)
        for i in range(start-1): # count and skip past rows alredy in file
            next(csvreader)
        row = next(csvreader)
        for row in csvreader:
            cur.execute("INSERT OR IGNORE INTO JRP (id,video_id,title,views,likes,dislikes,rating,guestid) VALUES (?,?,?,?,?,?,?,?)",(start,row[0],row[1],row[2],row[3],row[4],row[5],-1))
            start=start + 1
            #if 25 were added break
            if (start-1) % 25 == 0:
                break
    conn.commit()

#returns list of names from titles that are in the format (Joe Rogan Experience #1560 - Mike Baker)         
def getNames(cur):
    names = []
    cur.execute('SELECT title FROM JRP')
    titles = cur.fetchall()
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    #go through each title and use regex to get name only getting section name
    for title in titles:
        try:
            title = title[0]
            #guests = re.findall(regex,title)
            guests = re.split(',|&', pattern.match(title).group('name'))
            for person in guests:
                names.append(person.strip()) 
        except:
            #title is irregular or a small highlight clip
            pass
    return names

#count names and remove singles of guests
def countNames(names):
    returndict = dict()
    for person in names: 
        returndict[person] = returndict.get(person,0)+1
    return sorted(returndict.items(), key=lambda x: x[1], reverse=True)
    

#puts the names into file
def printNamesPretty(counts,file):
    dir = os.path.dirname(file)
    out_file = open(os.path.join(dir, file), "w")
    with open(file) as f:
        csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
        csv_writer.writerow(["Guest","Number Apperances"])
        for x in counts:
            csv_writer.writerow([x[0], x[1]])

#make seperate table for guests that appear more than once
def putNamesInData(counts,cur,conn):
    cur.execute('DROP TABLE IF EXISTS JRP_guest_count')
    cur.execute('CREATE TABLE JRP_guest_count (id INTEGER PRIMARY KEY, name TEXT, apperances INTEGER)')
    y=1
    for x in counts:
        cur.execute("INSERT INTO JRP_guest_count (id,name,apperances) VALUES (?,?,?)",(y,x[0],x[1]))
        y+=1
    conn.commit()

def fillGuestId(cur,conn):
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    cur.execute("""SELECT * FROM JRP""")
    results = cur.fetchall()
    for row in results:
        id=row[0] 
        title = row[2]
        
        names=[]
        try:
            guests = re.split(',|&', pattern.match(title).group('name'))
            for person in guests:
                names.append(person.strip())
        except:
            pass
        if(len(names)==1):
            cur.execute("SELECT id FROM JRP_guest_count WHERE JRP_guest_count.name = ?" , (names[0],))
            guestid = cur.fetchone()
            cur.execute("UPDATE JRP SET guestid = ? WHERE id = ?",(guestid[0],id))
        else:
            guestid=0
         
            #put guest id of 0 for exceptions of multiple people on episode, or a special clip
            cur.execute("UPDATE JRP SET guestid = ? WHERE id = ?",(guestid,id))
    conn.commit()

def barChartApperances(cur):
    # Initialize the plotcd
    fig = plt.figure(figsize=(10,4))
    ax1 = fig.add_subplot()   
    #making ax1
    l1 = dict()
    #select top 8 guests already in order 
    cur.execute('SELECT * FROM JRP_guest_count LIMIT 6')
    cur1 = cur.fetchall()
    for row in cur1:
        l1[row[1]]=row[2]

    people = []
    apperances=[]
    for key,value in l1.items():
        people.append(key)
        apperances.append(value)
    people = ['\n'.join(wrap(x, 16)) for x in people]
    ax1.bar(people,apperances,align='center', alpha=0.5, color='red')
    ax1.set(xlabel='Guest Name', ylabel='Apperances',
       title='8 Most Common Guests on JRP')
    ax1.set_xticklabels(people,FontSize='9')
    plt.show()
def barChart2(cur):
    fig = plt.figure(figsize=(10,4))
    ax2 = fig.add_subplot()   
    #make ax2 fist by finding 6 top episode
    cur.execute("SELECT views FROM JRP ORDER BY views DESC LIMIT 6")
    cur1 = cur.fetchall()
    views = []
    for x in cur1:
        views.append(x[0])
    guestname = []
    for x in views:
        cur.execute('SELECT JRP_guest_count.name FROM JRP LEFT JOIN JRP_guest_count ON JRP.guestid = JRP_guest_count.id WHERE JRP.views == ?',(x,))
        intm= cur.fetchone()
        guestname.append(intm[0])
    #if a value in 'None' due to two people on the episode, get the episode title instead 
        for x in range(len(guestname)):
            if(guestname[x]==None):
                cur.execute("SELECT title FROM JRP WHERE JRP.views == ?", (views[x],))
                title = cur.fetchone()
                guestname[x]=title[0]
    #make ax2
    guestname = ['\n'.join(wrap(x, 16)) for x in  guestname]
    ax2.bar(guestname,views,align='center', alpha=0.5, color='red')
    ax2.set(xlabel='Guest Name', ylabel='Episode views',
       title='Guests of the highest viewed episodes')
   
    ax2.ticklabel_format(useOffset=False, style='plain', axis='y')
    
    plt.show()

def pieChartMostViewedEps(cur):
    # get the most viewed eps title, like and disliked 
    # Data to plot
    cur.execute("SELECT title,likes,dislikes FROM JRP ORDER BY views DESC LIMIT 1")
    cur1 = cur.fetchall()
    
    episode = cur1[0][0]
    likes = cur1[0][1]
    dislikes = cur1[0][2]
    percLikes = likes/(likes+dislikes)
    prcDislikes = dislikes/(likes+dislikes)
    labels = ['likes (%d)'%likes,'dislikes (%d)'%dislikes]
    sizes = [percLikes,prcDislikes]
    colors = ['red','orange']
    
 
    # Plot
    #title1 = 'Most Viewed Episode %s likes to dislikes'%episode
    fig = plt.figure()
    ax1 = fig.add_subplot()
    plt.pie(sizes,  labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=14
       )
    ax1.set(title='Most Viewed Episode %s likes to dislikes'%episode)
 #title="Most Viewed Episode %s likes to dislikes" % (episode)
    plt.axis('equal')
    plt.show()



def main():
    cur, conn = setUpDatabase('JRP.db')
    #SECTION 1 - PUT AT LEAST 200 PEOPLE BEFORE GETTING APPERANCES/GUEST NAMES BELOW 
    uploadDataJRE(cur,conn)


    #SECTION 2 
    names = getNames(cur)   
    countedNames = countNames(names)
    printNamesPretty(countedNames, 'fileOutPutGuests.txt')
    putNamesInData(countedNames,cur,conn)

    #SECTION 3
    fillGuestId(cur,conn)

    #GRAPHS
    barChartApperances(cur)
    barChart2(cur)
    pieChartMostViewedEps(cur)

if __name__ == '__main__':
    main()
