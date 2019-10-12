import requests, bs4
from datetime import datetime

#parsing page with stories
def parseSubStoryPage(workinglink,lastcheck,finishlinks):
    r=requests.get(workinglink)
    b=bs4.BeautifulSoup(r.text,"html.parser")
    maxdate=lastcheck
    try:
        for i in b.find_all("article"):
            if (str(i.span.time.get("datetime"))>lastcheck):
                try:
                    finishlinks.add(i.img.get("src"))
                except:
                    finishlinks.add(i.video.get("src"))
                maxdate=str(i.span.time.get("datetime"))#stories are sorted by time, last story - max time
    except:
        pass
    return maxdate,finishlinks

#parsing https://storiesig.com/?username=username
def parseMainPage(j,lastdate):
    maxdate=lastdate
    finishlinks=set()
    lastcheck=lastdate
    workinglink="https://storiesig.com/?username="+j
    r=requests.get(workinglink)
    b=bs4.BeautifulSoup(r.text,"html.parser")
    try:
        if not((b.find("strong").getText()=="0 stories") or (b.find("strong").getText()=="This Account is Private")):
            workinglink="https://storiesig.com/stories/"+j
            lastcheck,finishlinks=parseSubStoryPage(workinglink,lastcheck,finishlinks)
            if (lastcheck>maxdate):
                maxdate=lastcheck
        for i in b.find_all("time"):
            lastcheck=lastdate
            if (str(i.get("datetime"))>lastdate):
                workinglink=str(i.parent.parent.get("href"))
                if not(workinglink=="None"):
                    workinglink="https://storiesig.com"+workinglink
                    lastcheck,finishlinks=parseSubStoryPage(workinglink,lastcheck,finishlinks)
                    if (lastcheck>maxdate):
                        maxdate=lastcheck
    except:
        pass
    return maxdate,finishlinks

#working with STORIES from ig
def ig(j, bot, conn, cursor):
    try:
        cursor.execute("SELECT date FROM stories WHERE igname = ?",(j,))
        cursor.fetchone()[0]#try to catch TypeError if no record with this igname
    except:
        cursor.execute("INSERT INTO stories VALUES(?,?)",(j,datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S.999Z"),))
        conn.commit()#write time
    cursor.execute("SELECT date FROM stories WHERE igname = ?",(j,))
    lastdate,finishlinks=parseMainPage(j,cursor.fetchone()[0])#return links to stories
    cursor.execute("DELETE FROM stories WHERE igname = ?",(j,))
    cursor.execute("INSERT INTO stories VALUES(?,?)",(j,lastdate,))
    conn.commit()#rewrite lastdate
    cursor.execute("SELECT tgid FROM subs WHERE igname = ?",(j,))
    for k in cursor.fetchall():
        for i in finishlinks:
            msgtext=j+' posted new <a href="'+i+'">story</a>'
            bot.sendMessage(k[0],msgtext,parse_mode= 'HTML')
    finishlinks.clear()