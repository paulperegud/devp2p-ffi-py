"""Python DevP2P example using parity's devp2p via FFI binding

Usage:
  ex2.py (--connect | --listen)

Options:
  -h, --help     Show this screen.
  -c, --connect     Connect to node listed in 'nodefile' file
  -l, --listen      Write your hostname into 'nodefile' and listen

"""
from docopt import docopt

from devp2p_ffi_py.service import *
import time
import threading

class Ex2(ProtocolFFI):
    def read(self, io_ptr, peer_id, packet_id, data):
        pass

    def connected(self, io_ptr, peer_id):
        print "connected: {}".format(peer_id)
        vsn = self.peer_protocol_version(io_ptr, peer_id)
        print "protocol version: {}".format(vsn)

def main(do_connect):
    with Service() as conn:
        conn.start()
        if do_connect:
            connect(conn)
        else:
            listen(conn)

def connect(conn):
    bp = Ex2()
    conn.add_subprotocol(bp)
    server = read_node_name()
    conn.add_reserved_peer(server)
    time.sleep(3)

def listen(conn):
    bp = Ex2()
    conn.add_subprotocol(bp)
    my_node_name = conn.node_name()
    write_node_name(my_node_name)
    time.sleep(10)

def read_node_name():
    with open('../devp2p/util/network/nodename', 'r') as f:
        node_name = f.read()
        return node_name

def write_node_name(node_name):
    with open('../devp2p/util/network/nodename', 'w') as f:
        f.write(node_name)

if __name__ == '__main__':
    arguments = docopt(__doc__)
    do_connect = arguments['--connect']
    main(do_connect)

