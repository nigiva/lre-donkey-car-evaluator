from loguru import logger

import socket 
import select
from threading import Thread
import time
from dcevaluator.utils.utils import build_log_tag

class BasicClient:
    def __init__(self, host = "127.0.0.1", 
                       port = 8080,
                       poll_socket_sleep_sec = 0.016,
                       buffer_message_size_read = 16 * 1024,
                       deltatime_to_compute_fps = 5.0
                       ):
        """
        Basic Client on the network 
        
        :param host: host to connect to a server like ip address with string
        :param port: port to connect to a server with int
        :param poll_socket_sleep_sec: time to sleep before polling socket
        :param buffer_message_size_read: number of bits to read into the socket
        :param delatime_to_compute_fps: deltatime between computation of the FPS
        """
        self.host = host
        self.port = port

        self.poll_socket_sleep_sec = poll_socket_sleep_sec
        self.buffer_message_size_read = buffer_message_size_read
        self.deltatime_to_compute_fps = deltatime_to_compute_fps

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

        self.readable_buffer = ""
        self.writable_buffer = ""

        self.nbr_frame_for_fps = 0
        self.first_frame_time = time.time()
    
    def connect(self):
        """
        Connect to the server
        """
        try:
            #Try to connect to a server
            self.socket.connect((self.host, self.port))
            logger.success(build_log_tag("CLIENT", "CONNECTED", host=self.host, port=self.port))
            self.connected = True
        except ConnectionRefusedError as e:
            self.connected = False
            logger.critical("Could not connect to server. Is it running? If you specified 'remote', then you must start it manually.")
            logger.critical(build_log_tag("CLIENT", "NOT CONNECTED", message="Could not connect to server. Is it running? If you specified 'remote', then you must start it manually."))
            raise RuntimeError(e)
        
        #Launch the processing loop to interpret in real time the message sent from the server
        self.loop_thread = Thread(target=self.loop)
        self.loop_thread.start()
    
    def loop(self):
        """
        Process the message sending or receiving with the server
        Works until the connection to the server is lost
        """
        # Check if the client is connected to a server
        if not self.connected:
            logger.error("Is not currently connected to a server !")
            logger.error(build_log_tag("CLIENT", "NOT CONNECTED", message="Is not currently connected to a server !"))
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
                self.process_readable_buffer()
                
            for writable_socket in writable_sockets_list:
                self.write_message_with_socket(writable_socket)
 
    def read_message_with_socket(self, readable_socket):
        """
        Fill the readable buffer with the message received from the server

        :param readable_socket: The readable socket
        """
        try:
            message = readable_socket.recv(self.buffer_message_size_read)
            message = message.decode("utf-8")
            self.readable_buffer += message

        except ConnectionAbortedError:
            logger.warn("Socket connection aborted")
            logger.warn(build_log_tag("CLIENT", "CONNECTION ABORTED", message="Socket connection aborted"))
            self.connected = False

    def write_message_with_socket(self, writable_socket):
        """
        Send the writable buffer to the server

        :param writable_socket: The writable socket
        """
        if self.writable_buffer != "":
            logger.trace("Sending : " + self.writable_buffer)
            writable_socket.sendall(self.writable_buffer.encode("utf-8"))
            logger.trace("Sent successfully : " + self.writable_buffer)
            self.writable_buffer = ""

    def process_readable_buffer(self):
        """
        Process the readable buffer in catching the complete requests
        i.e. select the message between two braces
        """
        first_brace_index = self.readable_buffer.find("{")
        last_brace_index = self.readable_buffer.rfind("}")

        #If we catch a complete request
        if first_brace_index >= 0 \
            and last_brace_index >= 0 \
            and first_brace_index < last_brace_index:

            select_requests = self.readable_buffer[first_brace_index:last_brace_index + 1]
            requests_list = select_requests.split("\n")

            #remove the selected resquests from the buffer
            self.readable_buffer = self.readable_buffer[last_brace_index + 1:]
            #Now, the current buffer contains the rest of the messages
            #which will process when the message is received completely (with end brace)

            for request in requests_list:
                self.on_request_receive(request)
            
    
    def send_message(self, message):
        """
        Send a message 
        Add `\n` at the end of the message and add all to the writable buffer.

        :param message: message to send
        """
        if self.writable_buffer != "":
            self.writable_buffer += "\n"
        self.writable_buffer = self.writable_buffer + message
    
    def send_now(self, message):
        self.socket.send(message.encode("utf-8"))

            
    def on_request_receive(self, request_string):
        """
        When the request is received

        :param request_string: request like a string
        """
        logger.trace("New request : ", request_string)

        #Compute FPS
        self.nbr_frame_for_fps += 1
        current_time = time.time()
        delta = current_time - self.first_frame_time
        if delta > self.deltatime_to_compute_fps:
            logger.debug(build_log_tag("FPS", fps=(self.nbr_frame_for_fps / delta)))
            self.nbr_frame_for_fps = 0
            self.first_frame_time = time.time()