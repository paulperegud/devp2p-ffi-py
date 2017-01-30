"""Python DevP2P pinger using parity's devp2p via FFI binding

Usage:
  pinger.py (--connect | --listen | --bootstrap)

Options:
  -h, --help     Show this screen.
  -c, --connect     Connect to node listed in 'nodefile' file
  -b, --bootstrap   Use node specified 'nodefile' file as boot_node
  -l, --listen      Write your hostname into 'nodefile' and listen

"""
from docopt import docopt

from devp2p_ffi_py.service import *
# import devp2p_ffi_py.service
import time
import threading

class PingPong(BaseProtocol):
    peer = None
    rx = [0,0,0,0,0,0]
    def __init__(self):
        BaseProtocol.__init__(self, "png", [1], 10)
    def read(self, io_ptr, peer_id, packet_id, data):
        with self.lock:
            self.rx[packet_id-1] += 1
            more = packet_id < len(self.rx)
        if more:
            time.sleep(0.01)
            self.reply(io_ptr, peer_id, packet_id+1, "z")

    def connected(self, _, peer_id):
        print "connected"
        self.peer = peer_id

def main(do_connect, do_bootstrap):
    conf = DevP2PConfig()
    if do_bootstrap:
        conf.boot_node = read_node_name()
    conf_ptr = conf.register()
    with DevP2P(conf_ptr) as conn:
        conn.start()
        if do_connect:
            connect(conn)
        else:
            listen(conn)

def connect(conn):
    bp = PingPong()
    N = 200
    conn.add_subprotocol(bp)
    server = read_node_name()
    conn.add_reserved_peer(server)
    time.sleep(3)
    if bp.peer is not None:
        for i in xrange(N):
            time.sleep(0.01)
            bp.send(bp.peer, 1, "z")
    time.sleep(5)
    with bp.lock:
        print bp.rx
        print sorted(set(bp.rx))
        res = [0, N] == sorted(set(bp.rx))
        assert res, "losing packets (https://github.com/ethcore/parity/issues/4107 ?)"

def listen(conn):
    bp = PingPong()
    conn.add_subprotocol(bp)
    my_node_name = conn.node_name()
    write_node_name(my_node_name)
    time.sleep(15)

def read_node_name():
    with open('nodename', 'r') as f:
        node_name = f.read()
        return node_name

def write_node_name(node_name):
    with open('nodename', 'w') as f:
        f.write(node_name)

if __name__ == '__main__':
    arguments = docopt(__doc__)
    do_connect = arguments['--connect']
    do_bootstrap = arguments['--bootstrap']
    main(do_connect, do_bootstrap)

