import zmq

def main():
    # Address for each server to receive files
    servAddresses = []
    names = []

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
            print("Done")

            if operation == b"List":
                username, filename, add = msg
                key = username+filename
                print(key, add)
                #names.append(username.decode("ascii"))
                #names.append([sha1.decode("ascii"), add.decode("ascii")])
                clients.send(b"DONE--")
            #print("------------{}".format(names))


            if operation == b"download":
                clients.send_multipart(servAddresses)

                #filename = msg
                #print(filename)
                #while True:
                #    f = open("proxy/index_{}.txt".format(filename.decode("ascii")), "rb")
                #    content = f.read(1024)

                #    while content:
                 #       clients.send_multipart([servAddresses, content])
                  #      content = f.read(1024)
                   # break
                    #f.close()

        if servers in socks:
            print("Message from server")
            operation, *rest = servers.recv_multipart()
            if operation == b"newServer":
                servAddresses.append(rest[0])
                print(servAddresses)
                servers.send(b"Ok")


if __name__ == '__main__':
    main()
