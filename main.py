# need pip3 install telepot, feedparser
import time
import telepot
import config
import sqlite3
import feedparser
from threading import Thread

AllOk=True#работаем пока True
time_OLD=time.time()#время последней проверки инсты
msg_list=[]#склад сообщений с телеги
f=open("message_id.txt","r")#последнее сообщение
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

#фоновая проверка входящих сообщений в телеге
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
                msg=chat+"%"+text
                msg_list.append(msg)
        except:
            pass

#обработка входящих сообщений из msg_list
def Message_Work():
    global cursor,conn,bot,AllOk,msg_list
    for msg in msg_list:
        chat=msg[:msg.find("%")]#извлечение данных сообщния со склада
        text=msg[msg.find("%")+1:]
        msg_list.remove(msg)#удаление прочитанного сообщения
        if ((text=="/stopBot") and (chat in config.admin_id)):
            AllOk=False;
            bot.sendMessage(chat,config.stopBot)
        elif (text=="/help"):
            bot.sendMessage(chat,config.help)
        elif (text=="/start"):
            bot.sendMessage(chat,config.start)
        else:
            if ((text[0:3]=="add") or(text[0:3]=="Add")):
                cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[4:],))
            elif ((text[0:3]=="del") or (text[0:3]=="Del")):
                cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(chat,text[4:],))
            else:
                cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text,))
            conn.commit()
            cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
            substring="Вы подписаны на \n"
            for i in cursor.fetchall():
                substring=substring+i[0]+"\n"
            bot.sendMessage(chat,substring)#вывод подписок
            substring=""

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
        global conn,cursor,bot
        parse_IG_posts(j,postid,posttext)
        cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
        if (postid <> cursor.fetchone()[0]):
            cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postid,))#перезапись ид последного поста
            conn.commit()
            msgtext=j+" posted new [photo](https://instagram.com/p/"+postid+")"+" with comment:\n"+"_"+posttext+"_"
            cursor.execute("SELECT tgid FROM subs WHERE igname=? ",(j,))
            for i in cursor.fetchall():
                bot.sendMessage(i[0],msgtext, Markdown)#расслыка тем, кто подписан на этот аккаунт

#общая работа с инстой
def Instagram_Work():
    global cursor
    allIGnicks=set()
    allIGnicks.clear()
    cursor.execute("SELECT igname FROM subs")
    for j in cursor.fetchall():
        allIGnicks.add(j[0])#сбор всех ников инсты в множество
    for j in allIGnicks:
        ig_posts(j)
        ig_stories(j)

#main
Thread(target=Telegram_checker).start()#в параллельном потоке в msg_list будут складываться входящие сообщения
while AllOk:
    Message_Work()
    if ((time.time()-time_OLD)>120):#раз в 2 мин проходимся по инсте
        time_OLD=time.time()
        Instagram_Work()

f=open("message_id.txt","w")#сохранение нужных данных перед выходом
f.write(str(m_id_old))
cursor.close()
