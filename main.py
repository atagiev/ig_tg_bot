import time
import config, database, stories, posts, message
from threading import Thread
from botapi import BotHandler
AllOk=True#program works while True
time_IG=time.time()#time of last Instagram check
msg_list=[]#archive of tamtam messages
bot=BotHandler(config.TOKEN)
conn,cursor=database.create()

#parallel thread to check new TamTam messages
def TamTam_checker():
    global bot,msg_list,AllOk
    while AllOk:
        try:
            upd=bot.get_updates(None)
            if upd != None:
                msg_list.append(upd["updates"][0]["message"])
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
Thread(target=TamTam_checker).start()#in a parallel thread messages are recorded in the archive msg_list
while AllOk:
    try:
        cursor, conn, AllOk, msg_list=message.work(cursor, conn, bot, AllOk, msg_list)
        if ((time.time()-time_IG)>4000): 
            time_IG=time.time()
            Instagram_Work()
    except:
        pass
cursor.close()
database.backup(bot)