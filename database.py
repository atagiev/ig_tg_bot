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
      cursor.execute("CREATE TABLE posts (igname text, timestamp integer)")#table Instagram name - id of last post
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
        urlretrieve(msg[2],"database.db")
    except:
        pass
    return create()

def backup(bot):
    try:
        bot.sendDocument(config.admin_id,open("database.db","rb"))
    except:
        pass

def clean(cursor, allIGnicks):
    #clean tables post && stories
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