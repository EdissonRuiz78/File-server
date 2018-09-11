import zmq
import sys
import hashlib
import json
import os
from random import randint

partSize = 1024 * 1024 * 10

def computeHashFile(filename):
    BUF_SIZE = 65536  
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def computeHash(bytes):
    sha1 = hashlib.sha1()
    sha1.update(bytes)
    return sha1.hexdigest()

def uploadFile(context, filename, servers, username):
    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://localhost:6666")

    indice = open("client/{}.txt".format(computeHashFile(filename.decode("ascii"))), "w")
    indice.close()    
    sockets = []

    for ad in servers:
        s = context.socket(zmq.REQ)
        s.connect("tcp://"+ ad.decode("ascii"))
        sockets.append(s)    
    with open(filename, "rb") as f:
        completeSha1= bytes(computeHashFile(filename), "ascii")
        finished = False
        part = 0
        while not finished:
            print("Uploading part {}".format(part))
            f.seek(part*partSize)
            bt = f.read(partSize)
            sha1bt = bytes(computeHash(bt), "ascii")
            indice = open("client/{}.txt".format(completeSha1.decode("ascii")), "a")
            s = sockets[part % len(sockets)]
            s.send_multipart([b"upload", filename, bt, sha1bt, completeSha1])
            s.recv()
            indice.write(bytes.decode(sha1bt, 'ascii'))
            indice.write("\n")
            indice.close()
            add = servers[part%len(sockets)]
            proxy.send_multipart([b"List key", completeSha1, sha1bt, add, bytes(str(part), ("ascii"))])
            proxy.recv()  
            print("Received reply for part {} ".format(part))
            part = part + 1
            if len(bt) < partSize:
                finished = True

        rand = randint(0, (len(servers)-1))
        s = sockets[rand]

        proxy.send_multipart([b"List", bytes(username, "ascii"), filename, servers[rand], completeSha1])
        proxy.recv()  
        while True:
            f = open("client/{}.txt".format(completeSha1.decode("ascii")), "rb")
            content = f.read(1024)
            while content:
                s.send_multipart([b"Index", completeSha1, content])
                content = f.read(1024)
            break
            f.close()
    os.remove("client/{}.txt".format(completeSha1.decode("ascii")))

def Download(context, values, filename):
    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://localhost:6666")
    
    indice = open("client/down-{}".format(filename.decode("ascii")), "w")
    indice.close()
    IP = values[0]
    SHA = values[1]
    server = context.socket(zmq.REQ)
    server.connect("tcp://{}".format(IP))

    server.send_multipart([ b"Down", bytes(SHA, ("ascii")), bytes(IP, ("ascii"))])
    message = server.recv()
    index = open("client/index-{}.txt".format(SHA), "wb")
    index.write(message)
    index.close()
    server.send(b"DONE")
    
    proxy.send_multipart([b"download-keys", bytes(SHA, ("ascii")), filename])
    shas = proxy.recv(1024)
    shas = json.loads(shas.decode())
    print(shas)
    
    for i in range(len(shas)):
        server = context.socket(zmq.REQ)
        server.connect("tcp://{}".format(shas[i][0]))
        server.send_multipart([b"Parts", bytes(shas[i][1], ("ascii")), filename])
        message = server.recv()
        index = open("client/down-{}".format(filename.decode("ascii")), "ab")
        index.write(message)
        index.close()
        server.send(b"DONE")

def Share(context, shas, username, filename):    
    key = username+filename.decode("ascii")
    values = shas.get(key)
    print("This is the key for you archive: {}".format(values[1]))
    #Download(context, values, filename)

def main():
    if len(sys.argv) != 4:
        print("Must be called with a filename")
        print("Sample call: python ftclient <username> <operation> <filename>")
        exit()

    username = sys.argv[1]
    operation = sys.argv[2]
    filename = sys.argv[3].encode('ascii')
    path = "client/"
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        pass
        
    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://localhost:6666")

    print("Operation: {}".format(operation))
    if operation == "upload":
        proxy.send_multipart([b"availableServers"])
        servers = proxy.recv_multipart()
        print("There are {} available servers".format(len(servers)))
        uploadFile(context, filename, servers, username)
        print("Username {} uploaded {}".format(username, filename.decode("ascii")))

    elif operation == "download":
        proxy.send_multipart([b"download", bytes(username, "ascii"), filename])
        shas = proxy.recv(1024)
        shas = json.loads(shas.decode())
        print(shas)
        Download(context, shas, filename)
        print("File {} downloaded".format(filename.decode("ascii")))

    elif operation == "share":
        proxy.send_multipart([b"share", bytes(username, "ascii"), filename])
        shas = proxy.recv(1024)
        shas = json.loads(shas.decode())
        Share(context, shas, username, filename)
        
    else:
        print("Operation not found!!!")

if __name__ == '__main__':
    main()