import devp2p_ffi_py.service
import devp2p_ffi_py.errors
from devp2p_ffi_py.cffi_devp2p import ffi, lib

import pytest
import time
import socket

def register(param, value):
    conf = service.Config()
    if hasattr(conf, param):
        setattr(conf, param, value)
    else:
        raise AttributeError("No such attribute!")
    conf.register()

def test_Configuration_config_path():
    register("config_path", "/tmp/devp2p_config_path")
    other_node = "enode://d742115276d73957a7b478d2b376eb02e183426827e3ab4ba483942d1421db4717350355099184bd823cbd29e1ca3fe4ceeb59a5bcb043655a2f8a4dfe3c129b@127.0.0.1:41223"
    register("boot_nodes", ["this is a boot node", other_node])
    with pytest.raises(errors.DevP2PNetworkError):
        conf_ptr = register("listen_address", "0.0.0.0")
    register("listen_address", "0.0.0.0:80")
    register("listen_address", "example.com:80")
    register("public_address", "8.8.8.8:12345")
    register("config_path", "cba")
    register("udp_port", 15)
    register("udp_port", 0)
    with pytest.raises(OverflowError):
        register("udp_port", -1)
    with pytest.raises(OverflowError):
        register("udp_port", 5 + 2**16)
    register("net_config_path", "abc")

def test_config_details():
    conf = service.Config()
    conf.config_path = "/tmp/devp2p_config_path"
    conf_ptr = conf.register()
    with service.Service(conf_ptr) as s:
        s.start()

def test_freeing():
    with service.Service() as s:
        pass
    with service.Service() as s:
        pass

def test_err_node_name():
    with service.Service() as s:
        assert s.node_name() is None

def test_add_subprotocol():
    bp = service.ProtocolFFI("abc", [1], 4)
    with service.Service() as s:
        s.add_subprotocol(bp)

def test_subprotocol_validation():
    service.ProtocolFFI("abc", [1,2,3,4,5,6], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("", [1], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("abcd", [1], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("abc", [1,3,300], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("abc", [-1], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("abc", [-1], 2)
    with pytest.raises(AssertionError):
        service.ProtocolFFI("abc", [1], -2)

def test_with_port():
    port = get_free_inet_port()
    assert not is_port_open(port)
    with service.Service(service.DevP2P.config_with_port(port)) as s:
        s.start() # <- this is slow
        assert is_port_open(port) # <- not this

def test_bind_to_inuse_port():
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    with service.Service(service.DevP2P.config_with_port(port)) as s:
        with pytest.raises(errors.DevP2PNetworkError):
            s.start()

def test_class():
    other_node = "enode://d742115276d73957a7b478d2b376eb02e183426827e3ab4ba483942d1421db4717350355099184bd823cbd29e1ca3fe4ceeb59a5bcb043655a2f8a4dfe3c129b@127.0.0.1:41223"
    with service.Service() as s:
        s.start()
        bp = service.ProtocolFFI("abc", [1], 2)
        s.add_subprotocol(bp)
        s.add_reserved_peer(other_node)

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
