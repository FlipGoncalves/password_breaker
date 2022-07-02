import pickle
from socket import socket

class Message:
    def __init__(self, json):
        self.converted = json

    def __str__(self):                  
        return pickle.dumps(self.converted)


class ConnectionMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, ip_address, ip_port):  
        self.id = identification
        self.__ip = ip_address
        self.__port = ip_port
        self.converted = { "command": "CONNECTION", "id": self.id, "ip": (self.__ip, self.__port) }
        super().__init__(self.converted)

class CoordenatorMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, ip_address, ip_port):   
        self.id = identification
        self.__ip = ip_address
        self.__port = ip_port
        self.converted = { "command": "COORDENATOR", "id": self.id, "ip": (self.__ip, self.__port) }
        super().__init__(self.converted)

class ScanMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, ip_address, ip_port):       # TODO: missing other arguments
        self.id = identification
        self.__ip = ip_address
        self.__port = ip_port
        self.converted = { "command": "SCANNING", "id": self.id, "ip": (self.__ip, self.__port) }
        super().__init__(self.converted)

class FailMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, pswd, idx):       # TODO: missing other arguments
        self.id = identification
        self.pswd = pswd
        self.idx = idx
        self.converted = { "command": "FAIL", "id": self.id, "pwd": self.pswd, "idx": self.idx }
        super().__init__(self.converted)

class SuccessMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, pswd):       # TODO: missing other arguments
        self.id = identification
        self.pswd = pswd
        self.converted = { "command": "SUCCESS", "pwd": self.pswd }
        super().__init__(self.converted)
        
class WorkMessage(Message):
    """Message to register username in the server."""
    def __init__(self, identification, pswd, count):       # TODO: missing other arguments
        self.id = identification
        self.pswd = pswd
        self.count = count
        self.converted = { "command": "WORKING", "id": self.id, "pwd": self.pswd, "idx": self.count }
        super().__init__(self.converted)
        

class Protocol:

    @classmethod
    def ConnectionMessage(cls, id: int, ip: str, port):
        """Creates a ConnectionMessage object."""
        message = ConnectionMessage(id, ip, port)
        return message

    @classmethod
    def CoordMessage(cls, id: int, ip: str, port):
        """Creates a CoordenatorMessage object."""
        message = CoordenatorMessage(id, ip, port)
        return message

    @classmethod
    def ScanMessage(cls, id: int, ip: str, port):
        """Creates a DiscoverMessage object."""
        message = ScanMessage(id, ip, port)
        return message
    
    @classmethod
    def FailMessage(cls, id: int, pswd: str, idx: int):
        """Creates a FailMessage object."""
        message = FailMessage(id, pswd, idx)
        return message

    @classmethod
    def SuccessMessage(cls, id: int, pswd: str): 
        """Creates a SuccessMessage object."""
        message = SuccessMessage(id, pswd)
        return message
    
    @classmethod
    def WorkMessage(cls, id: int, pswd: str, count: int): 
        """Creates a WorkMessage object."""
        message = WorkMessage(id, pswd, count)
        return message

    @classmethod
    def send_msg(cls, connection: socket, msg: Message, addr):
        """Sends through a connection a Message object."""
        connection.sendto(pickle.dumps(msg.converted), addr)   
        print(f"SENDING: {msg.converted}")      