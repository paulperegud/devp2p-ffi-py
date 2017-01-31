from cffi_devp2p import ffi, lib
from errors import *
import threading
import weakref

ffi_weakkeydict = weakref.WeakKeyDictionary()

class NonReservedPeerMode:
    ACCEPT = 1
    DENY = 2

class AllowIP:
    ALL = 1
    PRIVATE = 2
    PUBLIC = 3

class DevP2P():
    __protocols = []
    service = None
    config = None

    @staticmethod
    def config_local():
        return lib.config_local()

    @staticmethod
    def config_with_port(port):
        assert port > 0
        assert port < 2**16
        return lib.config_with_port(port)

    @staticmethod
    def service(config):
        errno = ffi.new("unsigned char *")
        service = lib.network_service(config, errno)
        if errno[0] != 0:
            raise DevP2PException("Can't initialize devp2p service instance")
        return service

    def __init__(self, config = None):
        if config == None:
            self.config = DevP2P.config_local()
            return
        self.config = config

    def __enter__(self):
        self.service = DevP2P.service(self.config)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        lib.network_service_free(self.service)
        self.service = None

    def start(self):
        res = lib.network_service_start(self.service)
        if res != 0:
            raise_errno(res, "Can't start service. Port in use?")

    def node_name(self):
        ptr = lib.network_service_node_name(self.service)
        if ffi.NULL == ptr:
            return None
        return ffi.string(ptr)

    def add_reserved_peer(self, node_name):
        mb_raise_errno(lib.network_service_add_reserved_peer(self.service, node_name))

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
        mb_raise_errno(err, "Failed to register a subprotocol")

"""Configuration for DevP2P Service"""
class DevP2PConfig():
    # Directory path to store general network configuration. None means nothing will be saved
    config_path = None # string
    # Directory path to store network-specific configuration. None means nothing will be saved
    net_config_path = None # string
    # IP address to listen for incoming connections. Listen to all connections by default
    listen_address = None # string
    # IP address to advertise. Detected automatically if none.
    public_address = None # string
    # Port for UDP connections, same as TCP by default
    udp_port = 0 # number; 0 means "use same as TCP"
    # Bootstrap node address; Parity's devp2p supports a list of boot_nodes; this FFI - not yet.
    boot_nodes = None # string

    """Obtain a pointer to configuration to use in DevP2P.service call"""
    def register(self):
        def make_boot_nodes(lst):
            if lst:
                pyarr = [ mk_str_len(bn) for bn in self.boot_nodes ]
                struct = ffi.new("struct StrLen *[]", pyarr)
                ptr = ffi.new("struct BootNodes*", (len(pyarr), struct))
                return ptr
            else:
                return ffi.NULL
        config_path = mk_str_len(self.config_path)
        net_config_path = mk_str_len(self.net_config_path)
        listen_address = mk_str_len(self.listen_address)
        public_address = mk_str_len(self.public_address)
        boot_nodes = make_boot_nodes(self.boot_nodes)
        zzz = (config_path,
               net_config_path,
               listen_address,
               public_address,
               self.udp_port,
               boot_nodes)
        conf = ffi.new("struct Configuration*", zzz)
        ffi_weakkeydict[conf] = (zzz)
        errno = ffi.new("unsigned char *")
        res = lib.config_detailed(conf, errno)
        mb_raise_errno(errno[0], "Bad arg while processing configuration")
        return res

def mk_str_len(string):
    if string is None:
        buff = ffi.NULL
    else:
        buff = ffi.from_buffer(string)
    size = ffi.sizeof(buff)
    res = ffi.new("struct StrLen*", (size, buff))
    ffi_weakkeydict[res] = (size, buff)
    return res

    # # Enable NAT configuration
    # nat_enabled = True
    # # Enable discovery
    # discovery_enabled = True
    # # Use provided node key instead of default
    # use_secret = None
    # # Minimum number of connected peers to maintain
    # min_peers = 25
    # # Maximum allowed number of peers
    # max_peers = 50
    # # Maximum handshakes
    # max_handshakes = 64
    # # Reserved protocols. Peers with <key> protocol get additional <value> connection slots.
    # reserved_protocols = {}
    # # List of reserved node addresses.
    # reserved_nodes = [] # strings
    # # The non-reserved peer mode.
    # non_reserved_mode = NonReservedPeerMode.ACCEPT
    # # IP filter
    # allow_ips = AllowIP.ALL

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
            raise_errno(errno[0], "Peer unknown or using wrong subprotocol")
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
