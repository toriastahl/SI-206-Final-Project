import re
import os
import numpy as np
import sqlite3
import youtube_dl
from tabulate import tabulate
import csv
import pandas
import matplotlib
import matplotlib.pyplot as plt

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

def getNames(file):
    names = []
    #use import pandas to make alist out of col
    colnames = ['id','title','view','likes','dislikes','rating']
    data = pandas.read_csv(file, names=colnames)
    titles = data.title.tolist()
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    #go through each title and use refex to get name
    for title in titles:
        try:
            guests = re.split(',|&', pattern.match(title).group('name'))
            for person in guests:
                names.append(person.strip()) 
        except:
            pass
    return names
#below is all the functions to pull the data from Youtube JRP
def getData():
    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})

    with ydl:
        ydl.params.update(ignoreerrors=True) #Dom Irrera's podcast is blocked on Copyright grounds
        result = ydl.extract_info(
            'https://www.youtube.com/playlist?list=UUzQUP1qoWDoEbmsQxvdjxgQ',
            download = False # We just want to extract the info
        )
    id = []
    titles = []
    views = []
    likes = []
    dislikes = []
    avg_rating = []
    guest_names = []
    for t in range(len(result['entries'])):
        try:
            id.append(result['entries'][t]['id'])
            titles.append(result['entries'][t]['title'])
            views.append(result['entries'][t]['view_count'])
            likes.append(result['entries'][t]['like_count'])
            dislikes.append(result['entries'][t]['dislike_count'])
            avg_rating.append(result['entries'][t]['average_rating'])
        except:
            pass
    dir = os.path.dirname('youtube_data.csv')
    out_file = open(os.path.join(dir, 'youtube_data.csv'), "w")

    #get guest names from titles
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    #go through each title and use refex to get name
    for title in titles:
        try:
            guests = re.split(',|&', pattern.match(title).group('name'))
            for person in guests:
                guest_names.append(person.strip()) 
        except:
            guest_names.append('N/A')
    #write data to csv file
    with open('youtube_data.csv') as f:
        csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
        csv_writer.writerow(["id","title","view","likes","dislikes","rating","guestid"])
        for x in range(len(titles)):
            try:
                cur.execute('SELECT id FROM JRP_guest_count WHERE name = ?',(guest_names[x], ))
                guestid = cur.fetchone()[0]
            except:
                guestid=-1
            csv_writer.writerow([id[x],titles[x],views[x],likes[x],dislikes[x],avg_rating[x],guestid])
    out_file.close()

def uploadDataJRE(cur,conn):

    cur.execute('DROP TABLE IF EXISTS Youtube_JRP')
    cur.execute('CREATE TABLE Youtube_JRP (video_id TEXT PRIMARY KEY, title TEXT, views INTEGER, likes INTEGER, dislikes INTEGER, rating REAL, guestid INTEGER)')
    with open('youtube_data.csv','r') as f:
        csvreader = csv.reader(f)
            # extracting field names through first row 
        fields = next(csvreader)
        for row in csvreader:
            cur.execute("INSERT INTO Youtube_JRP (video_id,title,views,likes,dislikes,rating,guestid) VALUES (?,?,?,?,?,?,?)",(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
    conn.commit()

    
def getNames(file):
    names = []
    #use import pandas to make alist out of col
    colnames = ['id','title','view','likes','dislikes','rating','guestid']
    data = pandas.read_csv(file, names=colnames)
    titles = data.title.tolist()
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    #go through each title and use refex to get name
    for title in titles:
        try:
            guests = re.split(',|&', pattern.match(title).group('name'))
            for person in guests:
                names.append(person.strip()) 
        except:
            pass
    return names

def countNames(names):
    #for big arrays 
    bigNames = np.array(names)
    sortedNames = np.sort(bigNames)
    #pandas software library function
    res = pandas.value_counts(sortedNames, sort=True)
    countNames = np.transpose(np.array([res.keys().to_numpy(),res.to_numpy()]))
    return countNames

def removeSingleNames(allNames):
    final = []
    #input is array in the form guest:num apperances
    for x in range(len(allNames)):
        #if there is only one apperance for a guest
        if allNames[x][1] == 1:
            final.append(x)
            #numpy.delete(arr, index, axis=None)
    allNames = np.delete(allNames, final, 0)
    return allNames


def printNamesPretty(counts):
    for guest in counts:
        print("|GUEST:| "+guest[0]+" |TIMES:| "+str(guest[1]))

def putNamesInData(counts,cur,conn):
    cur.execute('DROP TABLE IF EXISTS JRP_guest_count')
    cur.execute('CREATE TABLE JRP_guest_count (id INTEGER PRIMARY KEY, name TEXT, apperances INTEGER)')
    y=1
    for x in counts:
        cur.execute("INSERT INTO JRP_guest_count (id,name,apperances) VALUES (?,?,?)",(y,x[0],x[1]))
        y+=1
    conn.commit()

def barChartGuests(cur):
    # Initialize the plot
    fig = plt.figure()
    ax1 = fig.add_subplot(181)

    l1 = list()
    #select top 42 * from users
    cur.execute('SELECT * from JRP_guest_count LIMIT 8')
    for row in cur:
        l1.append(row)
    return l1

    #(names,values)
    people = list()
    apperances = list()
    people = [l1[0][1],l1[1][1],l1[2][1],l1[3][1],l1[4][1],l1[5][1],l1[6][1],l1[7][1]]
    apperances = [l1[0][2],l1[1][2],l1[2][2],l1[3][2],l1[4][2],l1[5][2],l1[6][2],l1[7][2]]
    ax1.bar(people,apperances)
    ax1.title('8 Most Common Guests on JRP')
    ax1.xlabel('Guest Name')
    ax1.ylabel('Apperances')

    # #make plot with Jack Dorsey episode show likes to dislikes ratio
    # ax2 = fig.add_subplot(182)

    # #find top 8 disliked episodes
    # l1 = list()
    # cur.execute('SELECT name,apperances FROM JRP_guest_count LEFT JOIN Categories ON Restaurants.category_id=Categories.id WHERE Restaurants.rating >= ? AND Categories.title == ? ',(rating,category))
    # for row in cur:
    #     l1.append(row)
    # return l1

    # #(names,values)
    # ax1.bar([l1[0][0],l1[1][0],l1[2][0],l1[3][0],l1[4][0],l1[5][0],l1[6][0],l1[7][0]],[l1[0][1],l1[1][1],l1[2][1],l1[3][1],l1[4][1],l1[5][1],l1[6][1],l1[7][1]])
    # ax1.title('8 Most Common Guests on JRP')
    # ax1.xlabel('Guest Name')
    # ax1.ylabel('Apperances')

    # Show the plot
    plt.show()


def main():
    #getting the names and counts of 
    names = getNames('youtube_data.csv')   
    countedNames = countNames(names)
    removedNames = removeSingleNames(countedNames) 
    printNamesPretty(removedNames)
    cur, conn = setUpDatabase('Youtube_JRP.db')
    putNamesInData(removedNames,cur,conn)

    
    #database set up 
    #cur, conn = setUpDatabase('Youtube_JRP.db')
    #Uncomment to download list from web (slow takes 25-30mins)
    #getData()
    #uploadDataJRE(cur,conn)
    #conn.close()

    #plot data

    barChartGuests(cur)


if __name__ == '__main__':
    main()