import time, telegram
import config, phrases, database, stories, posts
from threading import Thread

AllOk=True#program works while True
time_IG=time.time()#time of last Instagram check
msg_list=[]#archive of telegram messages
m_id_old=0
bot=telegram.Bot(token=config.TOKEN)
conn,cursor=database.create()

#parallel thread to check new Telegram messages
def Telegram_checker():
    global bot,msg_list,m_id_old,AllOk
    while AllOk:
        try:
            upd=bot.getUpdates(-1)
            msg_id=upd[0].message.message_id
            if (msg_id>m_id_old):
                m_id_old=msg_id
                chat=str(upd[0].message.chat.id)
                try:
                    text=upd[0].message.text
                    if text == None:
                        try:
                            if chat == config.admin_id:
                                msg=(chat,"database",bot.getFile(upd[0].message.document.file_id).file_path)
                                msg_list.append(msg)
                        except:
                            pass
                    else:
                        msg_list.append((chat,text))
                except:
                    pass
        except:
            pass

#send message with subscriptions
def subList(chat):
    global bot,cursor
    cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
    substring=phrases.substring
    for i in cursor.fetchall():
        substring=substring+i[0]+"\n"
    bot.sendMessage(chat,substring)

#processing incoming messages from msg_list
def Message_Work():
    global cursor,conn,bot,AllOk,msg_list
    for msg in msg_list:
        chat, text = msg[0], msg[1].lower()#working with archive of messages
        if ((text=="database") and (chat==config.admin_id)):
            conn, cursor = database.restore(msg,conn,cursor)
        elif ((text=="/stopbot") and (chat==config.admin_id)):
            AllOk=False
            bot.sendMessage(chat,phrases.stopBot)
        elif (text=="/help"):
            bot.sendMessage(chat,phrases.help)
        elif (text=="/start"):
            bot.sendMessage(chat,phrases.start)
        elif (text=="/sub"):
            subList(chat)
        elif ((text=="/backup") and (chat==config.admin_id)):
            database.backup(bot)
        elif (text[0:3]=="add"):
            try:
                cursor.execute("SELECT * FROM subs WHERE tgid = ? AND igname=?",(chat,text[3:].strip(),))
                cursor.fetchone()[0]
            except:
                cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[3:].strip(),))
            conn.commit()
            subList(chat)
        elif (text[0:3]=="del"):
            cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(chat,text[3:].strip(),))
            conn.commit()
            subList(chat)

        msg_list.remove(msg)#delete read message


#Working with Instagram
def Instagram_Work():
    global cursor
    allIGnicks=set()
    allIGnicks.clear()
    cursor.execute("SELECT igname FROM subs")
    for j in cursor.fetchall():
        allIGnicks.add(j[0])#collect all Ig names into set
    database.clean(cursor,allIGnicks)
    conn.commit()
    for j in allIGnicks:
        posts.ig(j, bot, conn, cursor)
        stories.ig(j, bot, conn, cursor)

#main
Thread(target=Telegram_checker).start()#in a parallel thread messages are recorded in the archive msg_list
while AllOk:
    try:
        Message_Work()
        if ((time.time()-time_IG)>120): #check Instagram every 2 minutes 
            time_IG=time.time()
            Instagram_Work()
    except:
        pass
cursor.close()
database.backup(bot)