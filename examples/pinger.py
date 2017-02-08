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
from devp2p_ffi_py.protocol import *
import time
import threading

class PingPong(BaseProtocol):
    protocol_id = "png"
    max_cmd_id = 2
    name = "Ping pong with TTL"
    version = 1

    rx = [0,0,0,0,0,0]
    lock = threading.Lock()

    def __init__(self, peer, protocolffi):
        super(PingPong, self).__init__(peer, protocolffi)
        ttl = len(self.rx)
        self.send_ping(ttl)

    class ping(BaseProtocol.command):
        cmd_id = 1
        structure = [
            ('ttl', sedes.big_endian_int)
        ]

        def create(self, proto, ttl):
            return dict(ttl=ttl)

        def receive(self, proto, data):
            ttl = data['ttl']
            with proto.lock:
                proto.rx[ttl-1] += 1
                print("{}->{}".format(ttl, proto.rx[ttl-1]))
            more = ttl-1 > 0
            if more:
                time.sleep(0.01)
                proto.send_ping(ttl-1)
            else:
                with proto.lock:
                    print proto.rx

def main(do_connect, do_bootstrap):
    conf = Config()
    if do_bootstrap:
        conf.boot_node = read_node_name()
    conf_ptr = conf.register()
    with Service(conf_ptr) as conn:
        conn.start()
        if do_connect:
            connect(conn)
        else:
            listen(conn)

def connect(conn):
    bp = ProtocolFFI(PingPong)
    conn.add_subprotocol(bp)
    server = read_node_name()
    conn.add_reserved_peer(server)
    time.sleep(9)

def listen(conn):
    bp = ProtocolFFI(PingPong)
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

