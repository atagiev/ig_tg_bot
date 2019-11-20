import requests, json, time

class BotHandler:

    def __init__(self, token):
        self.token = token
        self.url = 'https://botapi.tamtam.chat/'

    def get_updates(self, marker=None):
        method = 'updates'
        params = {
            "timeout": 45,
            "limit": 100,
            "marker": marker,
            "types": None,
            "access_token": self.token
        }
        try:
            response = requests.get(self.url + method, params)
            update = response.json()
        except:
            update = None
        if len(update['updates']) != 0:
            self.send_mark_seen(chat_id=self.get_chat_id(update))
        else:
            update = None
        return update

    def get_chat_id(self, update=None):
        chat_id = None
        if update == None:
            method = 'chats'
            params = {
                "access_token": self.token
            }
            response = requests.get(self.url + method, params)
            if response.status_code == 200:
                update = response.json()
                if 'chats' in update.keys():
                    update = update['chats'][0]
                    chat_id = update.get('chat_id')

        else:
            if 'updates' in update.keys():
                upd = update['updates'][0]
            else:
                upd = update
            if 'message_id' in upd.keys():
                chat_id = None
            elif 'chat_id' in upd.keys():
                chat_id = upd.get('chat_id')
            else:
                upd = upd.get('message')
                chat_id = upd.get('recipient').get('chat_id')
        return chat_id

    def send_mark_seen(self, chat_id):
        method_ntf = 'chats/{}'.format(chat_id) + '/actions?access_token='
        params = {"action": "mark_seen"}
        requests.post(self.url + method_ntf + self.token, data=json.dumps(params))

    def send_message(self, text, chat_id):
        return self.send_content(None, chat_id, text)

    def send_content(self, attachments, chat_id, text=None, link=None, notify=True):
        method = 'messages'
        params = (
            ('access_token', self.token),
            ('chat_id', chat_id),
        )
        data = {
            "text": text,
            "attachments": attachments,
            "link": link,
            "notify": notify
        }
        flag = 'attachment.not.ready'
        while flag == 'attachment.not.ready':
            response = requests.post(self.url + method, params=params, data=json.dumps(data))
            upd = response.json()
            if 'code' in upd.keys():
                flag = upd.get('code')
                time.sleep(5)
            else:
                flag = None
        if response.status_code == 200:
            update = response.json()
        else:
            update = None
        return update

    def send_file(self, content, chat_id, text=None, content_name=None):
        token = self.token_upload_content('file', content, content_name)
        attach = [{"type": "file", "payload": token}]
        update = self.send_content(attach, chat_id, text)
        return update

    def token_upload_content(self, type, content, content_name=None):
        url = self.upload_url(type)
        if content_name == None:
            content_name = content
        content = open(content, 'rb')
        response = requests.post(url, files={
            'files': (content_name, content, 'multipart/form-data')})
        if response.status_code == 200:
            token = response.json()
        else:
            token = None
        return token

    def upload_url(self, type):
        method = 'uploads'
        params = (
            ('access_token', self.token),
            ('type', type),
        )
        response = requests.post(self.url + method, params=params)
        if response.status_code == 200:
            update = response.json()
            url = update.get('url')
        else:
            url = None
        return url

