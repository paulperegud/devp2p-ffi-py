from cffi_devp2p import ffi, lib
import threading

class DevP2PException(Exception):
    pass

class UnknownPeer(DevP2PException):
    pass

class DevP2P():
    __protocols = []
    service = None

    @staticmethod
    def service():
        errno = ffi.new("unsigned char *")
        service = lib.network_service(errno)
        if errno[0] != 0:
            raise DevP2PException("Can't start devp2p service instance")
        return service

    def __enter__(self):
        self.service = DevP2P.service()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        lib.network_service_free(self.service)
        self.service = None

    def start(self):
        return lib.network_service_start(self.service)

    def node_name(self):
        ptr = lib.network_service_node_name(self.service)
        if ffi.NULL == ptr:
            return None
        return ffi.string(ptr)

    def add_reserved_peer(self, node_name):
        return lib.network_service_add_reserved_peer(self.service, node_name)

    def add_subprotocol(self, protocol):
        assert isinstance(protocol, BaseProtocol)
        userdata = ffi.new_handle(protocol)
        self.__protocols.append(userdata) # don't let the GC collect this!
        protocol.service = self.service
        protocol_id = ffi.new("char[]", protocol.id)
        buff = bytearray(protocol.versions)
        ffi_versions = ffi.from_buffer(buff)
        cbs = ffi.new("struct FFICallbacks*", (lib.initialize_cb,
                                               lib.connected_cb,
                                               lib.read_cb,
                                               lib.disconnected_cb))
        err = lib.network_service_add_protocol(self.service,
                                               userdata,
                                               protocol_id,
                                               protocol.max_packet_id,
                                               ffi_versions,
                                               len(buff),
                                               cbs
        )
        if err != 0:
            raise DevP2PException("Failed to register a subprotocol")
        return

class BaseProtocol():
    """
    Devp2p subprotocol definition.
    :member id: Subprotocol ID, can be represented by 3 chars
    :member name: Subprotocol name (not transmitted through the network)
    :member versions: array of numbers in 0..255 range, 1 uint8_t each
    :member max_packet_id: reserved space for commands
    """
    id = None
    name = ""
    versions = [1]
    max_packet_id = 0

    service = None
    lock = threading.Lock()

    def __init__(self, protocol_id, versions, max_packet_id, name = ""):
        assert len(protocol_id) == 3
        assert all([ v >= 0 and v <= 255 for v in versions ])
        self.versions = versions
        assert 1 <= max_packet_id and max_packet_id <= 255
        self.id = protocol_id
        self.max_packet_id = max_packet_id
        self.name = name

    def send(self, peer_id, packet_id, data_bytearray):
        assert packet_id <= self.max_packet_id
        buff = ffi.from_buffer(data_bytearray)
        size = ffi.sizeof(buff)
        protocol_id = ffi.new("char[]", self.id)
        lib.protocol_send(self.service, protocol_id, peer_id, packet_id, buff, size)

    def reply(self, context, peer_id, packet_id, data_bytearray):
        assert packet_id <= self.max_packet_id
        buff = ffi.from_buffer(data_bytearray)
        size = ffi.sizeof(buff)
        lib.protocol_reply(context, peer_id, packet_id, buff, size)

    def peer_protocol_version(self, context, peer_id):
        errno = ffi.new("unsigned char *")
        res = lib.peer_protocol_version(context, peer_id, errno)
        if errno[0] != 0:
            raise UnknownPeer("Peer unknown or using wrong subprotocol")
        return res

    # callbacks are below
    def initialize(self, io_ptr):
        pass

    def connected(self, io_ptr, peer_id):
        pass

    def read(self, io_ptr, peer_id, packet_id, data):
        pass

    def disconnected(self, io_ptr, peer_id):
        pass

# block of functions below route functional C-style callbacks to protocol objects
@ffi.def_extern()
def initialize_cb(userdata, io_ptr):
    protocol = ffi.from_handle(userdata)
    protocol.initialize(io_ptr)
    return

@ffi.def_extern()
def connected_cb(userdata, io_ptr, peer_id):
    protocol = ffi.from_handle(userdata)
    protocol.connected(io_ptr, peer_id)
    return

@ffi.def_extern()
def read_cb(userdata, io_ptr, peer_id, packet_id, data_ptr, length):
    data = ffi.unpack(data_ptr, length)
    protocol = ffi.from_handle(userdata)
    protocol.read(io_ptr, peer_id, packet_id, data)
    return

@ffi.def_extern()
def disconnected_cb(userdata, io_ptr, peer_id):
    protocol = ffi.from_handle(userdata)
    protocol.disconnected(io_ptr, peer_id)
    return
