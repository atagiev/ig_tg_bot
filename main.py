import time
import telepot
import config
import sqlite3
import feedparser
from threading import Thread

AllOk=True
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
def database_work():
    global cursor,conn,bot,m_id_old,AllOk
    while(AllOk):
        try:
            upd=bot.getUpdates(-1)
            m_id=upd[0]["message"]["message_id"]
            c_id=upd[0]["message"]["chat"]["id"]
            if (m_id>m_id_old):
                try:
                    text=upd[0]["message"]["text"]
                    if ((text=="/stopBot") and (c_id in config.admin_id)):
                        AllOk=False;
                    else:
                        if (text[0:3]=="add"):
                            cursor.execute("INSERT INTO subs VALUES(?,?)",(c_id,text[4:],))
                        if (text[0:3]=="del"):
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
def parseIGposts(igname,postid,posttext):
    workinglink="https://websta.me/rss/n/"+igname
    myfeed=feedparser.parse(workinglink)
    s=myfeed.entries[0]["link"]
    postid=s[26:37]
    s=myfeed.entries[0]["description"]
    posttext=s[:s.find("<a href=https://")]

#работа с новыми постами в ig
def ig_posts():
    global conn,cursor,bot,AllOk
    allIGnicks=set()
    while (AllOk):
        allIGnicks.clear()
        cursor.execute("SELECT igname FROM subs")
        for j in cursor.fetchall():
            allIGnicks.add(j[0])
        for j in allIGnicks:
            parseIGposts(j,postid,posttext)
            cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
            if (postid <> cursor.fetchone()[0]):
                cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
                cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postid,))
                conn.commit()
                msgtext=j+" posted new [photo](https://instagram.com/p/"+link+")"+" with comment:\n"+"_"+posttext+"_"#мб работает
                cursor.execute("SELECT tgid FROM subs WHERE igname=? ",(j,))
                for i in cursor.fetchall():
                    bot.sendMessage(i[0],msgtext, Markdown)

#обработка историй из иг
def ig_stories():
    pass


Thread(target = database_work).start()
time.sleep(1)
Thread(target = ig_posts).start()
Thread(target = ig_stories).start()
f=open("message_id.txt","w")
f.write(str(m_id_old))
cursor.close()
