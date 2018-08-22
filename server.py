import socket
import time
import datetime
from threading import Thread
import pickle
import json

class Server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    connections_dict = {} # dictionary with username as key socket as value

    HOST = 'localhost'
    PORT = 12345

    def __init__(self):
        self.s.bind((self.HOST,self.PORT))
        self.s.listen(3)
        accept = Thread(target=self.accept_clients) # no args
        accept.daemon = True
        accept.start()
        #accept.join()
        #self.s.close()

    def accept_clients(self):
        while True:
            # establish a connection
            clientsocket, address = self.s.accept()

            print(str(address[0]), "on port:", str(address[1]), "connected")
            username = clientsocket.recv(1024).decode('utf8')

            self.connections_dict[username] = clientsocket

            print(f'{username} on {address} connected')

            # this is the first thing that should happen not concurrently
            self.new_connection(username)


            thread = Thread(target=self.handle_client, args=[clientsocket, address, username])
            thread.daemon = True
            thread.start()


    def handle_client(self, clientsocket, address, username):
        while True:
            data = clientsocket.recv(2048)
            # %X Locale’s appropriate time representation. 07:06:05
            time_recieved = datetime.datetime.now().strftime("%X")

            if not data: # then socket is closed and person left
                print(username, "has disconnected")
                self.connections_dict.pop(username, None)
                name_fmt = '*'.rjust(10)
                msg = f'[{time_recieved}]{name_fmt}: {username} has left the chat'
                # msg = f'[{time_recieved}] *:  {username} has left the chat'

                alert = {username : False} # then person has left chat
                for connection in self.connections_dict.values():
                    connection.sendall(bytes(json.dumps(alert), 'utf8'))
                    time.sleep(.1) # need break or else both merge together
                    connection.sendall(bytes(msg, 'utf8'))
                clientsocket.close()
                break
            else: # then messages will be sent
                msg = data.decode('utf8')
                if len(msg) > 200: # too long a message
                    name_fmt = '*'.rjust(10)
                    msg = f"[{time_recieved}]{name_fmt}: Keep messages under 200 characters"
                    # msg = f"[{time_recieved}] *:  Keep messages under 200 characters
                    for connection in self.connections_dict.values():
                    # for connection in self.connections:
                        connection.sendall(bytes(msg, 'utf8'))
                else: # send message
                    # name_fmt = f'{username}'.rjust(10)
                    # msg = f"[{time_recieved}]{name_fmt}: {msg}"
                    # # msg = f"[{time_recieved}]  {username}:  {msg}"
                    for connection in list(self.connections_dict.values()):
                        if connection == clientsocket:
                            message = f"<html>[{time_recieved}] <font color='red'>{username}: </font>{msg}</html>"
                        else:
                            message = f"<html>[{time_recieved}] <font color='blue'>{username}: </font>{msg}</html>"

                        connection.sendall(bytes(message,'utf8'))

    # for every new connection notify that the person has joined the chat
    def new_connection(self, username):
        time_recieved = datetime.datetime.now().strftime("%X") # hr:min:s
        for connection in self.connections_dict.values():
            connection.sendall(bytes(json.dumps(list(self.connections_dict.keys())), 'utf8'))
            time.sleep(.1)
            name_fmt = '*'.rjust(10)
            msg = f'[{time_recieved}]{name_fmt}: {username} has joined the chat'
            # msg = f'[{time_recieved}]{name_fmt}:  {username} has joined the chat'
            connection.sendall(bytes(msg, 'utf8'))




server = Server()
server.accept_clients()
