import requests

#parsing all posts from instagram.com
def parse(j, timestamp):
    try:
        workinglink="https://instagram.com/"+j+"/?__a=1"
        r=requests.get(workinglink)
        postlinks=[]
        for i in r.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]:
            if i["node"]["taken_at_timestamp"]>timestamp:
                link="https://instagram.com/p/"+i["node"]["shortcode"]
                try:
                    msg=i["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                    postlinks.append((link,msg))
                except:
                    postlinks.append((link,))
            else:
                break
        try:
            newtimestamp=r.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]
        except:
            newtimestamp=timestamp
        return postlinks, newtimestamp
    except:
        return [], timestamp

#parse one last post from instagram.com
def parse_last(j):
    try:
        workinglink="https://instagram.com/"+j+"/?__a=1"
        r=requests.get(workinglink)
        return r.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]
    except:
        return 0

def msgtext(j,k):
    if len(k)==1:
        text=j+' posted new <a href="'+k[0]+'">photo</a>'
    else:
        text=j+' posted new <a href="'+k[0]+'">photo</a> with comment:\n<i>'+k[1]+'</i>'
    return text

#working with new POSTS from ig
def ig(j, bot, conn, cursor):
    try:
        try:
            cursor.execute("SELECT timestamp FROM posts WHERE igname = ?",(j,))
            cursor.fetchone()[0]#try to catch TypeError if no record with this igname
        except:
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j,parse_last(j),))
            conn.commit()#write timestamp instread of other to don't send post published before user send message to Telegram bot
        
        cursor.execute("SELECT timestamp FROM posts WHERE igname = ?",(j,))#last time
        timestamp=cursor.fetchone()[0]
        postlinks, newtimestamp=parse(j, timestamp)
        if newtimestamp > timestamp :
            cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j, newtimestamp,))#rewrite last time
            conn.commit()
        cursor.execute("SELECT tgid FROM subs WHERE igname = ?",(j,))
        for i in cursor.fetchall():#sending messages to followers
            for k in postlinks:
                bot.sendMessage(i[0],msgtext(j,k), parse_mode= 'HTML')
    except:
        pass