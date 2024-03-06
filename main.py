from cryptography.fernet import Fernet
import socket
import argparse
import sys

commands_cols = {
    "GMA": 'Midterm',
    "GEA": "Exam",
    "GL1A": "Lab 1",
    "GL2A": "Lab 2",
    "GL3A": "Lab 3",
    "GL4A": "Lab 4",
    "GG": None
}

command_msgs = {
    "GMA": 'Fetching midterm average: ',
    "GEA": "Fetching exams average: ",
    "GL1A": "Fetching lab 1 average: ",
    "GL2A": "Fetching lab 2 average: ",
    "GL3A": "Fetching lab 3 average: ",
    "GL4A": "Fetching lab 4 average: ",
    "GG": "Getting Grades: "
}

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
        print()

        # column titles
        keys = lines.pop(0).split(',')
        db = {}  # root dictionary
        for student_data in lines:
            student_data_list = student_data.split(',')
            student_dict = {}  # sub dictionary
            id = student_data_list[1]  # student id
            for i in range(len(student_data_list)):
                if i != 1:  # skip the id
                    student_dict[keys[i]] = student_data_list[i]
            db[id] = student_dict  # {id: student{}}
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
            print(f"Listening on port {self.PORT} ...")
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
            # If something bad happens, make sure that we close the socket.
            self.socket.close()
            print("Server shut down.")
            sys.exit(1)

    def connection_handler(self, client):
        # Unpack the client socket address tuple.
        connection, address_port = client
        address, port = address_port
        print("-" * 72)
        # Output the socket address.
        print(f"Connection received from {address} on port{port}.")

        while True:
            try:
                recvd_bytes = connection.recv(self.RECV_BUFFER_SIZE)

                if len(recvd_bytes) == 0:
                    connection.close()
                    print("Client connection closed.")
                    break

                recvd_str = recvd_bytes.decode("utf-8")
                recvd_str = recvd_str.strip().split()
                id_num, command = recvd_str[0], recvd_str[1]
                print(f"Received: {command} command from client.")

                #
                if self.db.get(id_num) is None:
                    print("User not found.")
                    connection.close()
                    print("Client connection closed.")
                    break
                print("User found.")
                student = self.db[id_num]
                encryption_key = student['Key']

                column = commands_cols[command]
                if command == "GG":
                    record_strings = [f"{key}: {value}" for key, value in student.items()]
                    # Joining the list into a single string, separated by commas
                    result = ", ".join(record_strings)
                elif command == "GEA":
                    grades = []
                    for record in self.db.values():
                        for i in range(1, 5):
                            grades.append(float(record[column + ' ' + str(i)]))
                    result = column + ' average: ' + str(sum(grades) / len(grades))
                else:
                    grades = []
                    for record in self.db.values():
                        grades.append(float(record[column]))
                    result = column + ' average: ' + str(sum(grades) / len(grades))
                print("Sending: \n", result)

                encryption_key_bytes = encryption_key.encode('utf-8')
                message_bytes = result.encode('utf-8')
                fernet = Fernet(encryption_key_bytes)
                encrypted_message_bytes = fernet.encrypt(message_bytes)
                connection.sendall(encrypted_message_bytes)

            except KeyboardInterrupt:
                connection.close()
                print("Client connection closed.")
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
        self.input_text = ""

    def read_and_clean_database_records(self):
        """Read and clean database records from a file."""
        db_file = "course_grades_2024.csv"
        try:
            with open(db_file, "r") as file:
                lines = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Database not found, creating: {db_file}")
            lines = []

        db = {}
        for student_data in lines:
            student_data_list = student_data.split(',')
            id, key = student_data_list[1], student_data_list[2]
            db[id] = key
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
            print(f"Connected to \"{Client.SERVER_HOSTNAME}\" on port {Client.PORT}")
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def send_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.connection_send()
                self.connection_receive()
            except (KeyboardInterrupt, EOFError):
                print()
                # If we get and error or keyboard interrupt, make sure that we close the socket.
                self.socket.close()
                print("Server connection closed.")
                sys.exit(1)

    def get_console_input(self):
        while True:
            self.input_text = input("Input: ")
            try:
                id_num, command = self.input_text.strip().split()
                command_msg = command_msgs.get(command)
                if command_msg is not None:
                    print(f"Command entered: {command}")
                    print(command_msg)
                    self.student_id = id_num
                    break
                print("Invalid command. Please try again.")
            except Exception as e:
                print("Error: ", e)

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
            encryption_key = self.db[str(self.student_id)]
            encryption_key_bytes = encryption_key.encode('utf-8')

            # Decrypt the message from the server.
            fernet = Fernet(encryption_key_bytes)
            decrypted_message_bytes = fernet.decrypt(recvd_bytes)
            decrypted_message = decrypted_message_bytes.decode('utf-8')

            print(decrypted_message)

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
