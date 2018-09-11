import zmq
import json

def main():
    # Address for each server to receive files
    servAddresses = []
    values = []
    list_keys = []
    keys_shas = {}
    keys_servers = {}
    
    context = zmq.Context()
    servers = context.socket(zmq.REP)
    servers.bind("tcp://*:5555")

    clients = context.socket(zmq.REP)
    clients.bind("tcp://*:6666")

    poller = zmq.Poller()
    poller.register(servers, zmq.POLLIN)
    poller.register(clients, zmq.POLLIN)

    while True:
        socks = dict(poller.poll())
        if clients in socks:
            print("Message from client")
            operation, *msg = clients.recv_multipart()

            if operation == b"availableServers":
                clients.send_multipart(servAddresses)
            
            elif operation == b"List":
                username, filename, add, CompleteSha = msg
                name = username.decode("ascii")
                files = filename.decode("ascii")
                key = name+files
                addr = add.decode("ascii")
                Sha1 = CompleteSha.decode("ascii")

                keys_servers = {"{}".format(key): [addr, Sha1]}
                clients.send(b"DONE--")
            
            elif operation == b"List key":
                CompleteSha, sha, add, part = msg
                key = CompleteSha.decode("ascii")
                sha1 = sha.decode("ascii")
                addr = add.decode("ascii")
                parts = int(part.decode("ascii"))
                
                if parts == 0:
                    values = []
            
                values.append([addr, sha1])
                keys_shas["{}".format(key)] = values
                           
                print(keys_shas)                
                clients.send(b"OK")

            elif operation == b"download":
                username, filename = msg
                name = username.decode("ascii")
                files = filename.decode("ascii")
                key = name+files
                values = keys_servers.get(key)
                print(values)
                data = json.dumps(values)
                clients.send(data.encode())
            
            elif operation == b"download-keys":
                SHA, filename = msg
                values = keys_shas.get(SHA.decode("ascii"))
                print(values)
                data = json.dumps(values)
                clients.send(data.encode())
            
            elif operation == b"share":
                username, filename = msg
                name = username.decode("ascii")
                files = filename.decode("ascii")
                key = name+files
                values = keys_servers.get(key)
                data = json.dumps(keys_servers)
                clients.send(data.encode())
        
        if servers in socks:
            print("Message from server")
            operation, *rest = servers.recv_multipart()
            if operation == b"newServer":
                servAddresses.append(rest[0])
                print(servAddresses)
                servers.send(b"Ok")

if __name__ == '__main__':
    main()
