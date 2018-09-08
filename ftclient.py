import zmq
import sys
import hashlib
from random import randint

partSize = 1024 * 1024 * 10

def uploadFile2(filename, socket):
    with open(filename, "rb") as f:
        finished = False
        part = 0
        while not finished:
            print("Uploading part {}".format(part))
            f.seek(part*partSize)
            bt = f.read(partSize)
            socket.send_multipart([filename, bt])
            response = socket.recv()
            print("Received reply  [%s ]" % (response))
            part = part + 1
            if len(bt) < partSize:
                finished = True

def computeHashFile(filename):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
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
    
    indice = open("client/{}_{}.txt".format(username, filename.decode("ascii")), "w")
    indice.write("{}\n".format(filename.decode("ascii")))
    indice.write("{}\n".format(computeHashFile(filename)))
    indice.close()
    
    sockets = []
    sha_list = []

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
            indice = open("client/{}_{}.txt".format(username, filename.decode("ascii")), "a")
            s = sockets[part % len(sockets)]
            s.send_multipart([b"upload", filename, bt, sha1bt, completeSha1])
            response = s.recv()
            indice.write(bytes.decode(sha1bt, 'ascii'))
            indice.write("\n")
            indice.close()
            #sha = bytes.decode(sha1bt, 'ascii')
            #add = servers[part%len(sockets)].decode("ascii")
            print("Received reply for part {} ".format(part))
            part = part + 1
            if len(bt) < partSize:
                finished = True

        rand = randint(0, (len(servers)-1))
        print(rand)
        s = sockets[rand]

        proxy.send_multipart([b"List", bytes(username, "ascii"), filename, servers[rand]])
        response1 = proxy.recv()  
        
        while True:
            f = open("client/{}_{}.txt".format(username, filename.decode("ascii")), "rb")
            content = f.read(1024)

            while content:
                s.send_multipart([b"Index", filename, bytes(username, "ascii"), content])
                content = f.read(1024)
            break
            f.close()


def Download(context, filename, servers, index):
    indice = open("client/down-index_{}.txt".format(filename.decode("ascii")), "w")
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
            indice = open("client/index_{}.txt".format(filename.decode("ascii")), "a")
            s = sockets[part % len(sockets)]
            s.send_multipart([b"upload", filename, bt, sha1bt, completeSha1])
            response = s.recv()
            indice.write(bytes.decode(sha1bt, 'ascii'))
            indice.write("\n")
            indice.close()
            print("Received reply for part {} ".format(part))
            part = part + 1
            if len(bt) < partSize:
                finished = True


def main():
    if len(sys.argv) != 4:
        print("Must be called with a filename")
        print("Sample call: python ftclient <username> <operation> <filename>")
        exit()


    username = sys.argv[1]
    operation = sys.argv[2]
    filename = sys.argv[3].encode('ascii')

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
        proxy.send_multipart([b"download"])
        servers = proxy.recv_multipart()
        print(servers)
        #Download(context, filename, servers)


        #index = open("client/down-index_{}.txt".format(filename.decode("ascii")), "wb")
        #index.write(index)
        #index.close()

        
        print("Not implemented yet")

    elif operation == "share":
        print("Not implemented yet")

    else:
        print("Operation not found!!!")

if __name__ == '__main__':
    main()
