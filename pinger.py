"""Python DevP2P pinger using parity's devp2p via FFI binding

Usage:
  pinger.py (--connect | --listen)

Options:
  -h, --help     Show this screen.
  -c, --connect     Connect to node listed in 'nodefile' file
  -l, --listen      Write your hostname into 'nodefile' and listen

"""
from docopt import docopt

import host
import time
import threading

class PingPong(host.BaseProtocol):
    peer = None
    rx = [0,0,0,0,0,0]
    def __init__(self):
        host.BaseProtocol.__init__(self, "png", [1])
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

def main(do_connect):
    with host.DevP2P() as conn:
        assert 0 == conn.start()
        if do_connect:
            connect(conn)
        else:
            listen(conn)

def connect(conn):
    bp = PingPong()
    N = 40
    conn.add_subprotocol(bp)
    server = read_node_name()
    assert 0 == conn.add_reserved_peer(server)
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
    if not res:
        print "still losing packets; see https://github.com/ethcore/parity/issues/4107"
        assert False

def listen(conn):
    bp = PingPong()
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
