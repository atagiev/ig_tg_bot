import feedparser

#parsing rss from https://queryfeed.net/instagram?q=username
def parse(j,lastlink):
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
def parse_last(j):
    workinglink="https://queryfeed.net/instagram?q="+j
    myfeed=feedparser.parse(workinglink)
    try:
        postlink=myfeed.entries[0].link
    except:
        postlink=""
    return postlink

#working with new POSTS from ig
def ig(j, bot, conn, cursor):
    try:
        cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))
        cursor.fetchone()[0]#try to catch TypeError if no record with this igname
    except:
        #write postid instread of other to don't send post published before user send message to Telegram bot
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,parse_last(j),))
        conn.commit()

    cursor.execute("SELECT postid FROM posts WHERE igname = ?",(j,))#last post link
    postlinks=parse(j,cursor.fetchone()[0])
    try:
        cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
        cursor.execute("INSERT INTO posts VALUES(?,?)",(j,postlinks[0][0],))#rewrite last post link
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
