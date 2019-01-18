# need pip3 install telepot, feedparser
import time
import telepot
import config
import sqlite3
import feedparser
#from threading import Thread

AllOk=True
time_OLD=time.time()
f=open("message_id.txt","r")
m_id_old=int(f.read())
bot=telepot.Bot(config.TOKEN)
conn=sqlite3.connect("database.db")
cursor=conn.cursor()
try:
    cursor.execute("CREATE TABLE subs (tgid text, igname text)")
except:
    pass
try:
    cursor.execute("CREATE TABLE posts (igname text, postid text)")
except:
    pass

#обработка входящих сообщений с тг и добавление ников в бд
def Telegram_Work():
    global cursor,conn,bot,m_id_old,AllOk
    try:
        upd=bot.getUpdates(-1)
        m_id=upd[0]["message"]["message_id"]
        c_id=upd[0]["message"]["chat"]["id"]
        if (m_id>m_id_old):
            try:
                text=upd[0]["message"]["text"]
                if ((text=="/stopBot") and (c_id in config.admin_id)):
                    AllOk=False;
                    bot.sendMessage(c_id,config.stopBot)
                elif (text=="/help"):
                    bot.sendMessage(c_id,config.help)
                elif (text=="/start"):
                    bot.sendMessage(c_id,config.start)
                else:
                    if ((text[0:3]=="add") or(text[0:3]=="Add")):
                        cursor.execute("INSERT INTO subs VALUES(?,?)",(c_id,text[4:],))
                    if ((text[0:3]=="del") or (text[0:3]=="Del")):
                        cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(c_id,text[4:],))
                    conn.commit()
                    cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(c_id,))
                    substring="Вы подписаны на \n"
                    for i in cursor.fetchall():
                        substring=substring+i[0]+"\n"
                    bot.sendMessage(c_id,substring)
                    substring=""
            except:
                pass
            m_id_old=m_id
    except:
        pass

#парсинг rss ленты с https://websta.me/rss/n/username
def parse_IG_posts(igname,postid,posttext):
    workinglink="https://websta.me/rss/n/"+igname
    myfeed=feedparser.parse(workinglink)
    s=myfeed.entries[0]["link"]
    postid=s[26:37]
    s=myfeed.entries[0]["description"]
    posttext=s[:s.find("<a href=https://")]

#работа с новыми постами в ig
def ig_posts(j):
        parse_IG_posts(j,postid,posttext)
        cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
        if (postid <> cursor.fetchone()[0]):
            cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postid,))
            conn.commit()
            msgtext=j+" posted new [photo](https://instagram.com/p/"+postid+")"+" with comment:\n"+"_"+posttext+"_"
            cursor.execute("SELECT tgid FROM subs WHERE igname=? ",(j,))
            for i in cursor.fetchall():
                bot.sendMessage(i[0],msgtext, Markdown)

def Instagram_Work():
    global conn,cursor,bot,AllOk
    allIGnicks=set()
    allIGnicks.clear()
    cursor.execute("SELECT igname FROM subs")
    for j in cursor.fetchall():
        allIGnicks.add(j[0])
    for j in allIGnicks:
        ig_posts(j)
        ig_stories(j)

#main
while AllOk:
    Telegram_Work()
    if ((time.time()-time_OLD)>120):
        time_OLD=time.time()
        Instagram_Work()

#Thread(target = Telegram_Work).start()
#Thread(target = Instagram_Work).start()
f=open("message_id.txt","w")
f.write(str(m_id_old))
cursor.close()
