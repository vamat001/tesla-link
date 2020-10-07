import web
from tesla import TeslaApi
import json

urls = (
    '/', 'webhook'
)


class webhook:

    def GET(self):
        return self.POST()

    def POST(self):
        web.header('Content-type', 'application/json')

        req = json.loads(web.data())
        handler = req['handler']['name']
        session = req['session']
        intent = req['intent']

        res = {}
        prompt = {}

        if handler == "loginHandler":
            try:
                t = TeslaApi()
                t.auth()
                output = t.wake()
                res['session'] = session
                res['session']['params'] = {'token': t.access_token, 'id': t.id, 'auth': True}
            except:
                output = "Unable to login"
                res['session'] = session
                res['session']['params'] = {'auth': False}

        elif handler == "dataHandler":
            try:
                token = session['params']['token']
                id = session['params']['id']
                auth = session['params']['auth']
                query = intent['params']['data']['resolved']
                if auth is True:
                    t = TeslaApi(token, id)
                else:
                    t = TeslaApi()
                output = t.dataHandler(query)
            except:
                output = "Something went wrong, please try again"

        elif handler == "commandHandler":
            try:
                token = session['params']['token']
                id = session['params']['id']
                auth = session['params']['auth']
                command = intent['params']['command']['resolved']
                limit = None
                if command == "set charge limit":
                    limit = intent['params']['charge_limit']['resolved']
                if auth is True:
                    t = TeslaApi(token, id)
                else:
                    t = TeslaApi()
                output = t.commandHandler(command, limit)
            except:
                output = "Something went wrong, please try again"

        elif handler == "exitHandler":
            try:
                token = session['params']['token']
                t = TeslaApi(token)
                t.revoke_auth()
                output = "Goodbye!"
            except:
                output = "Failed to revoke token"

        else:
            return "Invalid handler, please try again"

        prompt.update({'override': "true", 'firstSimple': {'speech': output, 'text': output}})
        res['prompt'] = prompt
        return json.dumps(res)
        # addr = t.location(car, key)


if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
