from loguru import logger

import socket 
import select
from threading import Thread
import time

class BasicClient:
    def __init__(self, host = "127.0.0.1", port = 8080):
        """
        Basic Client on the network 
        
        :arg host: host to connect to a server like ip address with string
        :arg port: port to connect to a server with int
        """
        self.host = host
        self.port = port

        self.poll_socket_sleep_sec = 0.016
        self.buffer_message_size_read = 10

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

        self.readable_buffer = ""
        self.writable_buffer = ""
    
    def connect(self):
        """
        Connect to the server
        """
        try:
            #Try to connect to a server
            self.socket.connect((self.host, self.port))
            logger.success("Client connected " + self.host + ":" + str(self.port))
            self.connected = True
        except ConnectionRefusedError as e:
            self.connected = False
            logger.critical("Could not connect to server. Is it running? If you specified 'remote', then you must start it manually. : \n" + str(e))
        
        #Launch the processing loop to interpret in real time the message sent from the server
        self.loop_thread = Thread(target=self.loop)
        self.loop_thread.start()
    
    def loop(self):
        """
        Process the sending or receiving message with the server
        Works until the connection to the server is lost
        """
        # Check if the client is connected to a server
        if not self.connected:
            logger.error("Is not currently connected to a server !")
            return

        self.socket.setblocking(False)

        while self.connected:
            #sleep because of a error on Windows
            time.sleep(self.poll_socket_sleep_sec)

            socket_list_to_talk = [ self.socket ]
            readable_sockets_list, writable_sockets_list, exceptional_sockets_list = select.select(socket_list_to_talk, socket_list_to_talk, socket_list_to_talk)

            #We get a single socket in the list (or an empty list sometimes)
            for readable_socket in readable_sockets_list:
                self.read_message_with_socket(readable_socket)
                #TODO Process the current readable buffer
                
            for writable_socket in writable_sockets_list:
                self.write_message_with_socket(writable_socket)
                #TODO create a function to add to the buffer some message

    def read_message_with_socket(self, readable_socket):
        """
        Fill the readable buffer with the message received from the server

        :arg readable_socket: The readable socket
        """
        message = readable_socket.recv(self.buffer_message_size_read)
        message = message.decode("utf-8")
        logger.trace(str(message))

        self.readable_buffer += message
        logger.trace(str(self.readable_buffer))

    def write_message_with_socket(self, writable_socket):
        """
        Send the writable buffer to the server

        :arg writable_socket: The writable socket
        """
        if self.writable_buffer != "":
            logger.info("Sending : " + self.writable_buffer)
            writable_socket.sendall(self.writable_buffer)
            logger.success("Sent successfully")
            self.writable_buffer = ""

