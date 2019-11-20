import phrases, database, config

#send message with subscriptions
def subList(bot, cursor, chat):
    cursor.execute("SELECT igname FROM subs WHERE ttid = ?",(chat,))
    substring=phrases.substring
    for i in cursor.fetchall():
        substring=substring+i[0]+"\n"
    bot.send_message(substring,chat)

#processing incoming messages from msg_list
def work(cursor,conn,bot,AllOk,msg_list):
    for msg in msg_list:
        chat=str(msg["recipient"]["chat_id"])#working with archive of messages
        text=(msg["body"]["text"]).lower()
        if ((text=='') and (chat==config.admin_chat_id)):
            conn, cursor = database.restore(msg,conn,cursor)
        elif ((text=="/stopbot") and (chat==config.admin_chat_id)):
            AllOk=False
            bot.send_message(phrases.stopBot,chat)
        elif (text=="/help"):
            bot.send_message(phrases.help,chat)
        elif (text=="/start"):
            bot.send_message(phrases.start,chat)
        elif (text=="/sub"):
            subList(bot, cursor, chat)
        elif ((text=="/backup") and (chat==config.admin_chat_id)):
            database.backup(bot)
        elif (text[0:3]=="add"):
            try:
                cursor.execute("SELECT * FROM subs WHERE ttid = ? AND igname=?",(chat,text[3:].replace(" ",""),))
                cursor.fetchone()[0]
            except:
                cursor.execute("INSERT INTO subs VALUES(?,?)",(chat,text[3:].replace(" ",""),))
            conn.commit()
            subList(bot, cursor, chat)
        elif (text[0:3]=="del"):
            cursor.execute("DELETE FROM subs WHERE (ttid= ?) AND (igname= ?)",(chat,text[3:].replace(" ",""),))
            conn.commit()
            subList(bot, cursor, chat)

        msg_list.remove(msg)#delete read message
    return cursor, conn, AllOk, msg_list

