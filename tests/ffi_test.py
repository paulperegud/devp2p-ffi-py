import unittest
import host
from cffi_devp2p import ffi, lib

class TestDevP2PFFI(unittest.TestCase):
    def test_ffi_basics(self):
        callback_hello_python = lib.hello_python
        assert 9 == lib.say_hello(callback_hello_python)
        x = lib.network_service()
        assert 0 == lib.network_service__start(x)
        assert 42 == lib.network_service__read_number(x)
        assert 42 == lib.network_service__read_number(x)
        assert 42 == lib.network_service__read_number(x)
        assert 42 == lib.network_service__read_number(x)
        assert 42 == lib.network_service__read_number(x)

    def test_class(self):
        other_node = "enode://d742115276d73957a7b478d2b376eb02e183426827e3ab4ba483942d1421db4717350355099184bd823cbd29e1ca3fe4ceeb59a5bcb043655a2f8a4dfe3c129b@127.0.0.1:41223"
        with host.DevP2P() as s:
            assert 0 == s.start()
            assert 0 == s.add_subprotocol()
            assert 0 == s.add_reserved_peer(other_node)
