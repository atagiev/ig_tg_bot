import time, telegram
import config, database, stories, posts, message
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
                msg_list.append(upd[0])
        except:
            pass

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
        cursor, conn, AllOk, msg_list=message.work(cursor, conn, bot, AllOk, msg_list)
        if ((time.time()-time_IG)>4000): #check Instagram every 4000 seconds 
            time_IG=time.time()
            Instagram_Work()
    except:
        pass
cursor.close()
database.backup(bot)