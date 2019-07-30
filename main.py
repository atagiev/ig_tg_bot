# need pip3 install telepot, feedparser, beautifulsoup4
import time
import telepot
import config
import phrases
import sqlite3
import feedparser
import requests
import bs4
from threading import Thread
from datetime import datetime

AllOk=True#program works while True
time_OLD=time.time()#time of last Instagram check
msg_list=[]#archive of telegram messages
m_id_old=0
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
                m_id_old=msg_id
                chat=upd[0]["message"]["chat"]["id"]
                try:
                    text=upd[0]["message"]["text"]
                    msg=(str(chat),text,)
                    msg_list.append(msg)
                except:
                    pass
        except:
            pass


#processing incoming messages from msg_list
def Message_Work():
    global cursor,conn,bot,AllOk,msg_list,m_id_old
    for msg in msg_list:
        chat=msg[0]#working with archive of messages
        text=msg[1].lower()
        msg_list.remove(msg)#delete read message
        if ((text=="/stopbot") and (chat == config.admin_id)):
            AllOk=False
            bot.sendMessage(chat,phrases.stopBot)
        elif (text=="/help"):
            bot.sendMessage(chat,phrases.help)
        elif (text=="/start"):
            bot.sendMessage(chat,phrases.start)
        elif (text=="/sub"):
            cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
            substring="You are subscribed to:\n"
            for i in cursor.fetchall():
                substring=substring+i[0]+"\n"
            bot.sendMessage(chat,substring)#send message with subscriptions
        elif ((text=="/backup")and (chat == config.admin_id)):
            try:
                bot.sendDocument(chat,open("database.db","rb"),caption=m_id_old)
            except:
                pass
        else:
            if (text[0:3]=="add"):
                try:
                    cursor.execute("SELECT * FROM subs WHERE tgid = ? AND igname=?",(chat,text[3:].strip(),))
                    cursor.fetchone()[0]
                except:
                    cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[3:].strip(),))
            elif (text[0:3]=="del"):
                cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(chat,text[3:].strip(),))
            if ((text[0:3]=="add") or (text[0:3]=="del")):
                conn.commit()
                cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
                substring="You are subscribed to:\n"
                for i in cursor.fetchall():
                    substring=substring+i[0]+"\n"
                bot.sendMessage(chat,substring)#send message with subscriptions

#parsing rss from https://queryfeed.net/instagram?q=username
def parse_IG_posts(j,lastlink):
    workinglink="https://queryfeed.net/instagram?q="+j
    myfeed=feedparser.parse(workinglink)
    postlinks=[]
    try:
        for i in myfeed.entries:
            if (i.link==lastlink):
                break
            tuple=(i.link,i.description,)
            postlinks.append(tuple)
    except:
        pass
    return postlinks

#parse one last post from https://queryfeed.net/instagram?q=username
def parse_last_post(j):
    workinglink="https://queryfeed.net/instagram?q="+j
    myfeed=feedparser.parse(workinglink)
    try:
        postlink=myfeed.entries[0].link
    except:
        postlink=""
    return postlink

#working with new POSTS from ig
def ig_posts(j):
    global conn,cursor,bot
    try:
        cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
        cursor.fetchone()[0]#try to catch TypeError if no record with this igname
    except:
        #write postid instread of other to don't send post published before user send message to Telegram bot
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,parse_last_post(j),))
        conn.commit()

    cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))#last post link
    postlinks=parse_IG_posts(j,cursor.fetchone()[0])
    try:
        postlink=postlinks[0][0]
        cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postlink,))#rewrite last post link
        conn.commit()
    except:
        pass
    cursor.execute("SELECT tgid FROM subs WHERE igname = ?",(j,))
    for i in cursor.fetchall():#sending messages to followers
        for k in postlinks:
            if (k[1]==""):
                msgtext=j+" posted new [photo]("+k[0]+")"
            else:
                msgtext=j+" posted new [photo]("+k[0]+") with comment:\n"+"_"+k[1]+"_"
            bot.sendMessage(i[0],msgtext, parse_mode= 'Markdown')

#parsing page with stories
def parseSubStoryPage(workinglink,lastcheck,finishlinks):
    r=requests.get(workinglink)
    b=bs4.BeautifulSoup(r.text,"html.parser")
    maxdate=lastcheck
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
        if not((b.find("strong").getText()=="0 stories") or (b.find("strong").getText()=="This Account is Private")):
            workinglink="https://storiesig.com/stories/"+j
            lastcheck,finishlinks=parseSubStoryPage(workinglink,lastcheck,finishlinks)
            if (lastcheck>maxdate):
                maxdate=lastcheck
        for i in b.find_all("time"):
            lastcheck=lastdate
            if (str(i.get("datetime"))>lastdate):
                workinglink=str(i.parent.parent.get("href"))
                if not(workinglink=="None"):
                    workinglink="https://storiesig.com"+workinglink
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
    try:
        Message_Work()
        if ((time.time()-time_OLD)>120):#check Instagram every 2 minutes
            time_OLD=time.time()
            Instagram_Work()
    except:
        pass
cursor.close()
bot.sendDocument(config.admin_id,open("database.db","rb"),caption=m_id_old)
