import zmq
import sys
import json
import os
import os.path

def main():
    if len(sys.argv) != 4:
        print("Sample call: python ftserver <address> <port> <folder>")
        exit()

    clientsPort = sys.argv[2]
    clientsAddress = sys.argv[1]
    serversFolder = sys.argv[3]
    clientsAddress = clientsAddress + ":" + clientsPort

    path = "{}".format(serversFolder)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        print("BE CAREFUL! Directory {} already exists.".format(path))

    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://localhost:5555")

    clients = context.socket(zmq.REP)
    clients.bind("tcp://*:{}".format(clientsPort))

    proxy.send_multipart([b"newServer", bytes(clientsAddress, "ascii")])
    m = proxy.recv()
    print(m)

    while True:
        print("Waitting for useres to upload!!!")
        operation, *rest = clients.recv_multipart()
        if operation == b"upload":
            filename, byts, sha1byts, sha1complete = rest
            storeAs = serversFolder + sha1byts.decode("ascii")
            print("Storing {}".format(filename))
            with open(storeAs, "wb") as f:
                f.write(byts)
            print("Uploaded as {}".format(filename))

        elif operation == b"Index":
            completeSha1, message = rest
            index = open("{}{}.txt".format(serversFolder, completeSha1.decode("ascii")), "wb")
            index.write(message)
            index.close()
        
        elif operation == b"Down":
            SHA, IP = rest
            ip = IP.decode("ascii")
            sha = SHA.decode("ascii")

            archivos = os.listdir("{}".format(serversFolder))
            for i in range (len(archivos)):
                if archivos[i] == "{}.txt".format(sha):
                    while True:
                        f = open("{}{}.txt".format(serversFolder, completeSha1.decode("ascii")), "rb")
                        content = f.read(1024)
                        while content:
                            clients.send(content)
                            content = f.read(1024)
                            clients.recv()
                        break
                        f.close()
                else:
                    pass
        
        elif operation == b"Parts":
            shas, filename = rest
            sha = shas.decode("ascii")
            archivos = os.listdir("{}".format(serversFolder))
            for i in range (len(archivos)):
                if archivos[i] == "{}".format(sha):
                    while True:
                        f = open("{}{}".format(serversFolder, sha), "rb")
                        content = f.read(1024*1024*10)

                        while content:
                            clients.send(content)
                            content = f.read(1024*1024*10)
                            clients.recv()
                        break
                        f.close()
                else:
                    pass

        else:
            print("Unsupported operation: {}".format(operation))

        clients.send(b"DONE")

if __name__ == '__main__':
    main()
