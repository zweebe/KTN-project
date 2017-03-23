# -*- coding: utf-8 -*-
import socketserver
import json
import re
import datetime
import time

"""
Variables and functions that must be used by all the ClientHandler objects
must be written here (e.g. a dictionary for connected clients)
"""
connected_clients = []
usernames = []
msg_log = []


class ClientHandler(socketserver.BaseRequestHandler):
    """
    This is the ClientHandler class. Everytime a new client connects to the
    server, a new ClientHandler object will be created. This class represents
    only connected clients, and not the server itself. If you want to write
    logic for the server, you must write it outside this class
    """

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request
        self.response = {'timestamp': '', 'sender': '', 'response': '', 'content': ''}
        self.logged_in = False
        self.username = ""

        # Loop that listens for messages from the client
        while True:
            received_string = self.connection.recv(4096).decode()
            data = json.loads(received_string)
            # data = received_string
            request = data["request"]

            #eneste som kan kjøres før logget inn
            if request == "login":
                if self in connected_clients:
                    self.send_response("", "error", "Du er allerede logget inn med brukernavn " + self.username)
                else:
                    self.login(data["content"])
            elif request == "help":
                self.help()
            elif not self.logged_in:
                self.send_response(self.username, 'error', 'Disse kommandoene kan kun brukes når man er logget inn')
            elif request == "logout":
                self.logout()
            elif request == "msg":
                self.message(data["content"])
            elif request == "names":
                self.names()

    def get_time_stamp(self):
        return str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def send_message(self, data):
        self.connection.sendall(json.dumps(data).encode())

    def send_response(self, sender, response, content):
        self.response['timestamp'] = self.get_time_stamp()
        self.response['sender'] = sender
        self.response['response'] = response
        self.response['content'] = content
        self.send_message(self.response)

    def help(self):
        help_txt = "Skriv login <brukernavn> for å logge in, logout for å logge ut, names for å få opp alle i chatten, " \
                   "skriv en melding for å sende eller hjelp for å returnere dette vinduet"
        self.send_response("", 'info', help_txt)

    def message(self, message):
        # add it to history
        msg_info = {'timestamp': self.get_time_stamp(), 'sender': self.username, 'response': 'history', 'content': message}
        msg_log.append(msg_info)
        # send msg to all clients
        for client in connected_clients:
            client.send_response(self.username, 'message', message)

    def logout(self):
        connected_clients.remove(self)
        usernames.remove(self.username)
        self.send_response("", 'info', ("Logget ut " + self.username))

    def login(self, username):
        # sjekk at brukernavn kun inneholder bokstaver og tall
        if not re.match(r'^[A-Za-z0-9]+$', username):
            self.send_response('', 'error', "Ugyldig brukernavn, prøv igjen")
        # logger inn og lagrer brukernavn
        elif (username not in usernames):
            self.username = username
            usernames.append(username)
            connected_clients.append(self)
            self.logged_in = True
            self.send_response("", 'info', "Du er nå logget inn med brukernavn " + username)
            self.send_history()
        # sier ifra at brukernavn finnes allerede
        else:
            self.send_response("", 'error', "Dette burkernavnet finnes allerede ;)")

    def names(self):
        names = ', '.join(name for name in usernames)
        self.send_response("", 'info', names)

    def send_history(self):
        for message in msg_log:
            self.send_message(message)
            time.sleep(0.1)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    This class is present so that each client connected will be ran as a own
    thread. In that way, all clients will be served by the server.

    No alterations are necessary
    """
    allow_reuse_address = True

if __name__ == "__main__":
    """
    This is the main method and is executed when you type "python Server.py"
    in your terminal.

    No alterations are necessary
    """
    HOST, PORT = '10.24.16.251', 9998
    print('Server running...')

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()