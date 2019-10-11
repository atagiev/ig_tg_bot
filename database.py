import sqlite3
import config
from urllib.request import urlretrieve

def create():
  conn = sqlite3.connect("database.db")#connecting database
  cursor = conn.cursor()
  try:
      cursor.execute("CREATE TABLE subs (tgid text, igname text)")#table telegram name - account in Instagram
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

def restore(bot,msg,conn,cursor):
    try:
        filename=msg.message.document.file_name
        if filename=="database.db":
            cursor.close()
            path=bot.getFile(msg.message.document.file_id).file_path
            urlretrieve(path,filename)
    except:
        pass
    return create()

def backup(bot):
    try:
        bot.sendDocument(config.admin_id,open("database.db","rb"))
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