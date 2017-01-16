import host
from cffi_devp2p import ffi, lib

import pytest
import time

def test_ffi_basics():
    x = host.DevP2P.service()
    assert 0 == lib.network_service_start(x)

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

def test_class():
    other_node = "enode://d742115276d73957a7b478d2b376eb02e183426827e3ab4ba483942d1421db4717350355099184bd823cbd29e1ca3fe4ceeb59a5bcb043655a2f8a4dfe3c129b@127.0.0.1:41223"
    with host.DevP2P() as s:
        assert 0 == s.start()
        bp = host.BaseProtocol("abc", [1], 2)
        s.add_subprotocol(bp)
        assert 0 == s.add_reserved_peer(other_node)
