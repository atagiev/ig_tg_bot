import sqlite3
import config
from urllib.request import urlretrieve

def create():
  conn = sqlite3.connect("database.db")#connecting database
  cursor = conn.cursor()
  try:
      cursor.execute("CREATE TABLE subs (ttid text, igname text)")#table tamtam id - account in Instagram
  except:
      pass
  try:
      cursor.execute("CREATE TABLE posts (igname text, timestamp integer)")#table Instagram name - timestamp of last post
  except:
      pass
  try:
      cursor.execute("CREATE TABLE stories (igname text, date text)")#table Instagram name - date of last story
  except:
      pass
  return conn, cursor

def restore(msg,conn,cursor):
    cursor.close()
    try:
        filename=msg["body"]["attachments"][0]["filename"]
        if filename=="database.db":
            path=msg["body"]["attachments"][0]["payload"]["url"]
            urlretrieve(path,filename)
    except:
        try:
            filename=msg["link"]["message"]["attachments"][0]["filename"]
            if filename=="database.db":
                path=msg["link"]["message"]["attachments"][0]["payload"]["url"]
                urlretrieve(path,filename)
        except:
            pass
    return create()

def backup(bot):
    try:
        bot.send_file("database.db",config.admin_chat_id)
    except:
        pass

#clean tables post && stories
def clean(cursor, allIGnicks):
    cursor.execute("SELECT * FROM posts")
    for i in cursor.fetchall():
        if not(i[0] in allIGnicks):
            try:
                cursor.execute("DELETE FROM posts WHERE igname=?",(i[0],))
            except:
                pass
    cursor.execute("SELECT * FROM stories")
    for i in cursor.fetchall():
        if not(i[0] in allIGnicks):
            try:
                cursor.execute("DELETE FROM stories WHERE igname=?",(i[0],))
            except:
                pass