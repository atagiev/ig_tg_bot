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
                msg=i["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                postlinks.append((link,msg))
            else:
                break
        try:
            timestamp=r.json()["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]
        except:
            timestamp=0
        return postlinks, timestamp
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


#working with new POSTS from ig
def ig(j, bot, conn, cursor):
    try:
        try:
            cursor.execute("SELECT timestamp FROM posts WHERE igname = ?",(j,))
            cursor.fetchone()[0]#try to catch TypeError if no record with this igname
        except:
            #write timestamp instread of other to don't send post published before user send message to Telegram bot
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j,parse_last(j),))
            conn.commit()
    
        cursor.execute("SELECT timestamp FROM posts WHERE igname = ?",(j,))#last time
        timestamp=cursor.fetchone()[0]
        postlinks,newtimestamp=parse(j,timestamp)
        if newtimestamp > timestamp :
            cursor.execute("DELETE FROM posts WHERE igname = ?",(j,))
            cursor.execute("INSERT INTO posts VALUES(?,?)",(j,newtimestamp,))#rewrite last time
            conn.commit()
        cursor.execute("SELECT tgid FROM subs WHERE igname = ?",(j,))
        for i in cursor.fetchall():#sending messages to followers
            for k in postlinks:
                if (k[1]==""):
                    msgtext=j+" posted new [photo]("+k[0]+")"
                else:
                    msgtext=j+" posted new [photo]("+k[0]+") with comment:\n"+"_"+k[1]+"_"
                bot.sendMessage(i[0],msgtext, parse_mode= 'Markdown')
    except:
        pass