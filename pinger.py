from host import DevP2P
import time

def main():
    with DevP2P() as active:
        active.start()
        active.add_subprotocol()
        server = get_node_name()
        print "nodename: {}".format(server)
        active.add_reserved_peer(server)
        time.sleep(10)

def get_node_name():
    with open('../devp2p/util/network/nodename', 'r') as f:
        node_name = f.read()
        return node_name

if __name__ == '__main__':
    main()

