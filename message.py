import phrases, database, config

#send message with subscriptions
def subList(bot, cursor, chat):
    cursor.execute("SELECT igname FROM subs WHERE tgid = ?",(chat,))
    substring=phrases.substring
    for i in cursor.fetchall():
        substring=substring+i[0]+"\n"
    bot.sendMessage(chat,substring)

#processing incoming messages from msg_list
def work(cursor,conn,bot,AllOk,msg_list):
    for msg in msg_list:
        chat=str(msg.message.chat.id)#working with archive of messages
        try:
            text=(msg.message.text).lower()
        except:
            text=msg.message.text
        if ((text==None) and (chat==config.admin_id)):
            conn, cursor = database.restore(bot,msg,conn,cursor)
        elif ((text=="/stopbot") and (chat==config.admin_id)):
            AllOk=False
            bot.sendMessage(chat,phrases.stopBot)
        elif (text=="/help"):
            bot.sendMessage(chat,phrases.help)
        elif (text=="/start"):
            bot.sendMessage(chat,phrases.start)
        elif (text=="/sub"):
            subList(bot, cursor, chat)
        elif ((text=="/backup") and (chat==config.admin_id)):
            database.backup(bot)
        elif (text[0:3]=="add"):
            try:
                cursor.execute("SELECT * FROM subs WHERE tgid = ? AND igname=?",(chat,text[3:].replace(" ",""),))
                cursor.fetchone()[0]
            except:
                cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[3:].replace(" ",""),))
            conn.commit()
            subList(bot, cursor, chat)
        elif (text[0:3]=="del"):
            cursor.execute("DELETE FROM subs WHERE (tgid= ?) AND (igname= ?)",(chat,text[3:].replace(" ",""),))
            conn.commit()
            subList(bot, cursor, chat)

        msg_list.remove(msg)#delete read message
    return cursor, conn, AllOk, msg_list