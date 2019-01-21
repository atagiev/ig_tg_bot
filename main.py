# need pip3 install telepot, feedparser, beautifulsoup4
import time
import telepot
import config
import sqlite3
import feedparser
import requests
import bs4
from threading import Thread
from datetime import datetime

AllOk=True#program works while True
logOn=False#if True - logs are enabled
time_OLD=time.time()#time of last Instagram check
msg_list=[]#archive of telegram messages
f=open("message_id.txt","r")#last telegram message
m_id_old=int(f.read())
bot=telepot.Bot(config.TOKEN)
conn=sqlite3.connect("database.db")#connecting database
cursor=conn.cursor()
try:
    cursor.execute("CREATE TABLE subs (tgid text, igname text)")#table telegram name - account in Instagram
except:
    pass
try:
    cursor.execute("CREATE TABLE posts (igname text, postid text)")#table Instagram name - id of last post
except:
    pass
try:
    cursor.execute("CREATE TABLE stories (igname text, date text)")#table Instagram name - date of last story
except:
    pass

#parallel thread to check new Telegram messages
def Telegram_checker():
    global bot,msg_list,m_id_old,AllOk
    while AllOk:
        try:
            upd=bot.getUpdates(-1)
            msg_id=upd[0]["message"]["message_id"]
            if (msg_id>m_id_old):
                chat=upd[0]["message"]["chat"]["id"]
                try:
                    text=upd[0]["message"]["text"]
                except:
                    pass
                m_id_old=msg_id
                msg=str(chat)+"%"+text
                msg_list.append(msg)
        except:
            pass

#send logs to admins
def Log_Send(msg):
    global bot,logOn
    if logOn:
        for i in config.admin_id:
            bot.sendMessage(i,msg)

#processing incoming messages from msg_list
def Message_Work():
    global cursor,conn,bot,AllOk,msg_list,logOn
    for msg in msg_list:
        chat=msg[:msg.find("%")]#working with archive of messages
        text=msg[msg.find("%")+1:]
        msg_list.remove(msg)#delete read message
        if (((text=="/stopBot") or (text=="/stopbot")) and (chat in config.admin_id)):
            AllOk=False;
            bot.sendMessage(chat,config.stopBot)
        elif (text=="/help"):
            bot.sendMessage(chat,config.help)
        elif (text=="/start"):
            bot.sendMessage(chat,config.start)
        elif ((text=="/log") and (chat in config.admin_id)):
            if logOn:
                Log_Send(config.logmsgOff)
                logOn=not logOn
            else:
                logOn=not logOn
                Log_Send(config.logmsgOn)
        else:
            if ((text[0:3]=="add") or(text[0:3]=="Add")):
                try:
                    cursor.execute("SELECT * FROM subs WHERE tgid = ? AND igname=?",(chat,text[4:],))
                    cursor.fetchone()[0]
                except:
                    cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[4:],))
            elif ((text[0:3]=="del") or (text[0:3]=="Del")):
                cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(chat,text[4:],))
            if ((text[0:3]=="add") or (text[0:3]=="Add") or (text[0:3]=="del") or (text[0:3]=="Del")):
                conn.commit()
                cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
                substring="Вы подписаны на:\n"
                for i in cursor.fetchall():
                    substring=substring+i[0]+"\n"
                bot.sendMessage(chat,substring)#send message with subscriptions
                substring=""

#parsing rss from https://websta.me/rss/n/username
def parse_IG_posts(igname):
    workinglink="https://websta.me/rss/n/"+igname
    myfeed=feedparser.parse(workinglink)
    s=myfeed.entries[0]["link"]
    postid=s[26:37]
    s=myfeed.entries[0]["description"]
    posttext=s[:s.find("<a href=https://")]
    return postid,posttext

#working with new POSTS from ig
def ig_posts(j):
    global conn,cursor,bot
    try:
        workinglink="https://instagram.com/"+j
        postid,posttext=parse_IG_posts(workinglink)
    except:
        postid,posttext="",""
    try:
        cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
        cursor.fetchone()[0]#try to catch TypeError if no record with this igname
    except:
        #write postid instread of other to don't send post published before user send message to Telegram bot
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postid,))
        conn.commit()
    cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
    if not(postid == cursor.fetchone()[0]):
        cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postid,))#rewrite last post id
        conn.commit()
        msgtext=j+" posted new [photo](https://instagram.com/p/"+postid+")"+" with comment:\n"+"_"+posttext+"_"
        cursor.execute("SELECT tgid FROM subs WHERE igname=? ",(j,))
        for i in cursor.fetchall():#sending messages to followers
            try:
                bot.sendMessage(i[0],msgtext, parse_mode= 'Markdown')
            except:
                pass

#parsing page with stories
def parseSubStoryPage(workinglink,lastcheck,finishlinks):
    r=requests.get(workinglink)
    b=bs4.BeautifulSoup(r.text,"html.parser")
    try:
        for i in b.find_all("article"):
            if (str(i.span.time.get("datetime"))>lastcheck):
                try:
                    finishlinks.add(i.img.get("src"))
                except:
                    finishlinks.add(i.video.get("src"))
                maxdate=str(i.span.time.get("datetime"))#stories are sorted by time, last story - max time
    except:
        pass
    return maxdate,finishlinks

#parsing https://storiesig.com/?username=username
def parseMainPageIgStory(j,lastdate):
    maxdate=lastdate
    finishlinks=set()
    lastcheck=lastdate
    workinglink="https://storiesig.com/?username="+j
    r=requests.get(workinglink)
    b=bs4.BeautifulSoup(r.text,"html.parser")
    try:
        if not(b.find("strong").getText()=="0 stories"):
            workinglink="https://storiesig.com/stories/"+j
            lastcheck,finishlinks=parseSubStoryPage(workinglink,lastcheck,finishlinks)
            if (lastcheck>maxdate):
                maxdate=lastcheck
        for i in b.find_all("time"):
            lastcheck=lastdate
            if (str(i.get("datetime"))>lastdate):
                workinglink="https://storiesig.com"+str(i.parent.parent.get("href"))
                lastcheck,finishlinks=parseSubStoryPage(workinglink,lastcheck,finishlinks)
                if (lastcheck>maxdate):
                    maxdate=lastcheck
    except:
        pass
    return maxdate,finishlinks

#working with STORIES from ig
def ig_stories(j):
    global bot,conn,cursor
    try:
        cursor.execute("SELECT date FROM stories WHERE igname = ?",(j,))
        cursor.fetchone()[0]#try to catch TypeError if no record with this igname
    except:
        cursor.execute("INSERT INTO stories VALUES(?,?)",(j,datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S.999Z"),))
        conn.commit()#write time
    cursor.execute("SELECT date FROM stories WHERE igname = ?",(j,))
    lastdate=cursor.fetchone()[0]
    lastdate,finishlinks=parseMainPageIgStory(j,lastdate)#return links to stories
    cursor.execute("DELETE FROM stories WHERE igname = ?",(j,))
    cursor.execute("INSERT INTO stories VALUES(?,?)",(j,lastdate,))
    conn.commit()#rewrite lastdate
    cursor.execute("SELECT tgid FROM subs WHERE igname = ?",(j,))
    for k in cursor.fetchall():
        for i in finishlinks:
            msgtext=j+" posted new [story]("+i+")"
            bot.sendMessage(k[0],msgtext,parse_mode= 'Markdown')
    finishlinks.clear()

#Working with Instagram
def Instagram_Work():
    global cursor
    allIGnicks=set()
    allIGnicks.clear()
    cursor.execute("SELECT igname FROM subs")
    for j in cursor.fetchall():
        allIGnicks.add(j[0])#collect all Ig names into set
    #clean tables post && stories
    cursor.execute("SELECT * FROM posts")
    for i in cursor.fetchall():
        if not(i[0] in allIGnicks):
            try:
                cursor.execute("DELETE FROM posts WHERE igname=?",(i[0],))
            except:
                pass
    cursor.execute("SELECT * FROM stories")
    for i in cursor.fetchall():
        if not(i[0] in allIGnicks):
            try:
                cursor.execute("DELETE FROM stories WHERE igname=?",(i[0],))
            except:
                pass
    for j in allIGnicks:
        ig_posts(j)
        ig_stories(j)

#main
Thread(target=Telegram_checker).start()#in a parallel thread messages are recorded in the archive msg_list
while AllOk:
    Message_Work()
    if ((time.time()-time_OLD)>120):#check Instagram every 2 minutes
        time_OLD=time.time()
        Instagram_Work()
        Log_Send(config.logmsgInstagramCheck)

f=open("message_id.txt","w")#saving important data before exit
f.write(str(m_id_old))
f.close()
cursor.close()
Log_Send(config.logmsgBotOff)
