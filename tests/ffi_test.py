import socket

import host
from cffi_devp2p import ffi, lib

import pytest
import time

def test_freeing():
    with host.DevP2P() as s:
        pass
    with host.DevP2P() as s:
        pass

def test_err_node_name():
    with host.DevP2P() as s:
        assert s.node_name() is None

def test_add_subprotocol():
    bp = host.BaseProtocol("abc", [1], 4)
    with host.DevP2P() as s:
        s.add_subprotocol(bp)

def test_subprotocol_validation():
    host.BaseProtocol("abc", [1,2,3,4,5,6], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("", [1], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("abcd", [1], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("abc", [1,3,300], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("abc", [-1], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("abc", [-1], 2)
    with pytest.raises(AssertionError):
        host.BaseProtocol("abc", [1], -2)

def test_with_port():
    port = get_free_inet_port()
    assert not is_port_open(port)
    with host.DevP2P(host.DevP2P.config_with_port(port)) as s:
        s.start() # <- this is slow
        assert is_port_open(port) # <- not this

def test_bind_to_inuse_port():
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    with host.DevP2P(host.DevP2P.config_with_port(port)) as s:
        with pytest.raises(host.NetworkError):
            s.start()

def test_class():
    other_node = "enode://d742115276d73957a7b478d2b376eb02e183426827e3ab4ba483942d1421db4717350355099184bd823cbd29e1ca3fe4ceeb59a5bcb043655a2f8a4dfe3c129b@127.0.0.1:41223"
    with host.DevP2P() as s:
        s.start()
        bp = host.BaseProtocol("abc", [1], 2)
        s.add_subprotocol(bp)
        assert 0 == s.add_reserved_peer(other_node)

# helper functions
def get_free_inet_port():
    for port in xrange(49152, 65535):
        if not is_port_open(port):
            return port

def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0
