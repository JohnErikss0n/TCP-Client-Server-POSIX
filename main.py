import cryptography
from cryptography.fernet import Fernet
import socket
import argparse
import sys
import math

class Server:

    def __init__(self):
        self.HOSTNAME = "0.0.0.0"  # All interfaces.
        self.PORT = 50000  # Server port to bind the listen socket.
        self.RECV_BUFFER_SIZE = 2048  # Used for recv.
        self.MAX_CONNECTION_BACKLOG = 10  # Used for listen.
        self.SOCKET_ADDRESS = (self.HOSTNAME, self.PORT)

        self.db = self.read_and_clean_database_records()

        self.create_listen_socket()
        self.process_connections_forever()

    def import_student_database(self):
        """Read and process the student database."""
        self.read_and_clean_database_records()
        self.parse_student_records()

    def read_and_clean_database_records(self):
        """Read and clean database records from a file."""
        db_file = "course_grades_2024.csv"
        try:
            with open(db_file, "r") as file:
                lines = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Database not found, creating: {db_file}")
            lines = []


        print("Data read from CSV file: ")
        for line in lines:
            print(line)


        keys = lines.pop(0).split(',')
        db = {}
        for student_data in lines:
            student_data_list = student_data.split(',')
            student_dict = {}
            id = student_data_list[1]
            for i in range(len(student_data_list)):
                if i!=1:
                    student_dict[keys[i]] = student_data_list[i]
            db[id] = student_dict
        return db

    def create_listen_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set socket layer socket options. This one allows us to
            # reuse the socket address without waiting for any timeouts.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to socket address, i.e., IP address and port.
            self.socket.bind(self.SOCKET_ADDRESS)

            # Set socket to listen state.
            self.socket.listen(self.MAX_CONNECTION_BACKLOG)
            print("Listening on port {} ...".format(self.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def process_connections_forever(self):
        try:
            while True:
                # Block while waiting for accepting incoming TCP
                # connections. When one is accepted, pass the new
                # (cloned) socket info to the connection handler
                # function. Accept returns a tuple consisting of a
                # connection reference and the remote socket address.
                self.connection_handler(self.socket.accept())
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            # If something bad happens, make sure that we close the
            # socket.
            self.socket.close()
            sys.exit(1)

    def connection_handler(self, client):
        # Unpack the client socket address tuple.
        connection, address_port = client
        print("-" * 72)
        print("Connection received from {}.".format(address_port))
        # Output the socket address.
        print(client)

        while True:
            try:
                recvd_bytes = connection.recv(self.RECV_BUFFER_SIZE)

                if len(recvd_bytes) == 0:
                    print("Closing client connection ... ")
                    connection.close()
                    break

                recvd_str = recvd_bytes.decode("utf-8")
                print("Received: ", recvd_str)
                recvd_str = recvd_str.strip().split()
                id_num, command = recvd_str[0],recvd_str[1]



                encryption_key = self.db[id_num]['Key']



                commands = {
                    "GMA": 'Midterm',
                    "GEA": "Exam",
                    "GL1A": "Lab 1" ,
                    "GL2A": "Lab 2",
                    "GL3A": "Lab 3",
                    "GL4A": "Lab 4",
                    "GG": None
                }
                command_mapped = commands[command]
                result = "Error, command not recognized"

                if command not in commands.keys():
                    print("Error, command not recognized")
                elif command == "GG":
                    record = self.db[id_num]
                    command_strings = [f"{key}: {value}" for key, value in record.items()]
                    # Joining the list into a single string, separated by commas
                    joined_string = ", ".join(command_strings)
                    result = joined_string
                elif command == "GEA":
                    grades = []

                    for key in self.db:
                        for i in range(1,5):
                            print(key+' '+str(i))
                            grades.append(float(self.db[key][command_mapped+' '+str(i)]))
                    result = command_mapped+ ' average: '+str(sum(grades)/len(grades))

                else:
                    grades = []
                    for key in self.db:
                        grades.append(float(self.db[key][command_mapped]))
                    result = command_mapped+ ' average: '+str(sum(grades)/len(grades))


                encryption_key_bytes = encryption_key.encode('utf-8')

                message_bytes = result.encode('utf-8')

                fernet = Fernet(encryption_key_bytes)
                encrypted_message_bytes = fernet.encrypt(message_bytes)
                connection.sendall(encrypted_message_bytes)

            except KeyboardInterrupt:
                print()
                print("Closing client connection ... ")
                connection.close()
                break


class Client:

    SERVER_HOSTNAME = "localhost"
    RECV_BUFFER_SIZE = 1024  # Used for recv.
    PORT = 50000

    def __init__(self):
        self.get_socket()
        self.connect_to_server()
        self.db = self.read_and_clean_database_records()


        self.send_console_input_forever()
        self.student_id = 0


    def read_and_clean_database_records(self):
        """Read and clean database records from a file."""
        db_file = "course_grades_2024.csv"
        try:
            with open(db_file, "r") as file:
                lines = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Database not found, creating: {db_file}")
            lines = []



        keys = lines.pop(0).split(',')
        db = {}
        for student_data in lines:
            student_data_list = student_data.split(',')
            db[student_data_list[1]] = student_data_list[2]
        return db

    def get_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Allow us to bind to the same port right away.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the client socket to a particular address/port.
            # self.socket.bind((Server.HOSTNAME, 40000))

        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connect_to_server(self):
        try:
            # Connect to the server using its socket address tuple.
            self.socket.connect((Client.SERVER_HOSTNAME, self.PORT))
            print("Connected to \"{}\" on port {}".format(Client.SERVER_HOSTNAME, self.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def get_console_input(self):
        # In this version we keep prompting the user until a non-blank
        # line is entered, i.e., ignore blank lines.
        while True:
            self.input_text = input("Input: ")
            if self.input_text != "":
                self.student_id = self.input_text.split()[0]
                break

    def send_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.connection_send()
                self.connection_receive()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                # If we get and error or keyboard interrupt, make sure
                # that we close the socket.
                self.socket.close()
                sys.exit(1)

    def connection_send(self):
        try:
            # Send string objects over the connection. The string must
            # be encoded into bytes objects first.
            self.socket.sendall(self.input_text.encode('utf-8'))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_receive(self):
        try:
            # Receive and print out text. The received bytes objects
            # must be decoded into string objects.
            recvd_bytes = self.socket.recv(Client.RECV_BUFFER_SIZE)

            # recv will block if nothing is available. If we receive
            # zero bytes, the connection has been closed from the
            # other end. In that case, close the connection on this
            # end and exit.
            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)
            encryption_key = self.db[self.student_id]
            encryption_key_bytes = encryption_key.encode('utf-8')

            # Encrypt the message for transmission at the server.
            fernet = Fernet(encryption_key_bytes)
            decrypted_message_bytes = fernet.decrypt(recvd_bytes)
            decrypted_message = decrypted_message_bytes.decode('utf-8')

            print("Received: ", decrypted_message)

        except Exception as msg:
            print(msg)
            sys.exit(1)
if __name__ == '__main__':
    roles = {'client': Client, 'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles,
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()