import time
import telepot
import config
import sqlite3
from threading import Thread
#connect ig library
AllOk=True
f=open("message_id.txt","r")
m_id_old=int(f.read())
bot=telepot.Bot(config.TOKEN)
conn=sqlite3.connect("database.db")
cursor=conn.cursor()
try:
    cursor.execute("CREATE TABLE a (id text, igname text)")#возможно стоит хранить дату последнего обновления иг
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
                            cursor.execute("INSERT INTO a VALUES(?,?)",(c_id,text[4:],))
                        if (text[0:3]=="del"):
                            cursor.execute("DELETE FROM a WHERE (id= ?) AND (igname= ?)",(c_id,text[4:],))
                        conn.commit()
                        cursor.execute("SELECT igname FROM a WHERE id = ?",(c_id,))
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

#работа с новыми постами и историями из ig
def ig_checker():
    global conn,cursor,bot,AllOk
    allIGnicks=set()
    while (AllOk):
        allIGnicks.clear()
        cursor.execute("SELECT igname FROM a")
        for j in cursor.fetchall():
            allIGnicks.add(j[0])
        #тут пройтись по множеству и чекнуть иг


Thread(target = database_work).start()
time.sleep(1)
Thread(target = ig_checker).start()
f=open("message_id.txt","w")
f.write(str(m_id_old))
cursor.close()
