from cffi_devp2p import ffi, lib
from errors import *
import threading
import weakref

from devp2p_ffi_py.peer import Peer
from devp2p_ffi_py.protocol import Packet

ffi_weakkeydict = weakref.WeakKeyDictionary()

class NonReservedPeerMode(object):
    ACCEPT = 1
    DENY = 2

class AllowIP(object):
    ALL = 1
    PRIVATE = 2
    PUBLIC = 3

class Service(object):
    protocol_handles = {}
    protocols = {}
    ns = None # FFI NetworkService
    config = None

    peers = {} # currently connected peers

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
        ns = lib.network_service(config, errno)
        if errno[0] != 0:
            raise DevP2PException("Can't initialize devp2p service instance")
        return ns

    def __init__(self, config = None):
        if config == None:
            self.config = Service.config_local()
            return
        self.config = config

    def __enter__(self):
        self.ns = Service.service(self.config)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        lib.network_service_free(self.ns)
        self.ns = None

    def start(self):
        res = lib.network_service_start(self.ns)
        if res != 0:
            raise_errno(res, "Can't start service. Port in use?")

    def node_name(self):
        ptr = lib.network_service_node_name(self.ns)
        if ffi.NULL == ptr:
            return None
        return ffi.string(ptr)

    def add_reserved_peer(self, node_name):
        mb_raise_errno(lib.network_service_add_reserved_peer(self.ns, node_name))

    def disconnect_peer(self, peer_id, ban = False):
        """NetworkContext.{disable|disconnect}_peer"""
        raise NotImplemented()

    def add_subprotocol(self, protocol):
        assert isinstance(protocol, ProtocolFFI)
        userdata = ffi.new_handle(protocol)
        self.protocols[protocol.protocol_id] = protocol
        self.protocol_handles[protocol.protocol_id] = userdata # don't let the GC collect this!
        protocol.service = self
        protocol_id = ffi.new("char[]", protocol.protocol_id)
        buff = bytearray(protocol.versions)
        ffi_versions = ffi.from_buffer(buff)
        cbs = ffi.new("struct FFICallbacks*", (lib.initialize_cb,
                                               lib.connected_cb,
                                               lib.read_cb,
                                               lib.disconnected_cb))
        err = lib.network_service_add_protocol(self.ns,
                                               userdata,
                                               protocol_id,
                                               protocol.max_packet_id,
                                               ffi_versions,
                                               len(buff),
                                               cbs
        )
        mb_raise_errno(err, "Failed to register a subprotocol")

    def register_peer(self, protocol, peer_id):
        if self.peers.has_key(peer_id):
            peer = self.peers[peer_id]
            peer.add_protocol(protocol)
        else:
            peer = Peer(self, peer_id)
            self.peers[peer_id] = peer
            peer.add_protocol(protocol)
        return peer

    def deregister_peer(self, protocol, peer_id):
        if self.peers.has_key(peer_id):
            peer = self.peers[peer_id]
            peer.rem_protocol(protocol)
        else:
            peer = Peer(self, peer_id)
            self.peers[peer_id] = peer
            peer.rem_protocol(protocol)
        if len(peer.protocols) == 0:
            del self.peers[peer_id]

"""Thin wrapper around subprotocol FFI callbacks"""
class ProtocolFFI(object):
    """
    Callbacks
    :member protocol_id: Subprotocol ID, can be represented by 3 chars
    :member name: Subprotocol name (not transmitted through the network)
    :member versions: array of numbers in 0..255 range, 1 uint8_t each
    :member max_packet_id: reserved space for commands
    """
    protocol_id = None
    name = ""
    versions = [1]
    max_packet_id = 0

    service = None
    decoder_klass = None
    peers = {} # peer_id -> instance of decoder_klass
    lock = threading.Lock()

    def __init__(self, decoder_klass):
        self.decoder_klass = decoder_klass
        self.protocol_id = decoder_klass.protocol_id
        self.versions = [ decoder_klass.version ]
        self.max_packet_id = decoder_klass.max_cmd_id
        self.name = decoder_klass.name
        ProtocolFFI.validate(self.protocol_id, self.versions, self.max_packet_id)

    @classmethod
    def validate(cls, protocol_id, versions, max_packet_id):
        assert len(protocol_id) == 3
        assert all([ v >= 0 and v <= 255 for v in versions ])
        assert 1 <= max_packet_id and max_packet_id <= 255

    def send_packet(self, peer_id, packet_id, data_bytearray):
        assert packet_id <= self.max_packet_id
        buff = ffi.from_buffer(data_bytearray)
        size = ffi.sizeof(buff)
        protocol_id = ffi.new("char[]", self.protocol_id)
        lib.protocol_send(self.service.ns, protocol_id, peer_id, packet_id, buff, size)

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
        protocolffi = self
        peer = self.service.register_peer(protocolffi, peer_id)
        decoder = self.decoder_klass(peer, self)
        self.peers[peer_id] = decoder

    def read(self, io_ptr, peer_id, packet_id, data):
        decoder = self.peers[peer_id]
        packet = Packet(protocol_id = decoder.protocol_id, cmd_id = packet_id, payload = data)
        decoder.receive_packet(packet)

    def disconnected(self, io_ptr, peer_id):
        protocol = self
        self.service.deregister_peer(protocol, peer_id)

# block of functions below route functional C-style callbacks to protocol objects
@ffi.def_extern()
def initialize_cb(userdata, io_ptr):
    protocol = ffi.from_handle(userdata)
    protocol.initialize(io_ptr)
    return

@ffi.def_extern()
def connected_cb(userdata, io_ptr, peer_id):
    print("python: connected")
    protocol = ffi.from_handle(userdata)
    protocol.connected(io_ptr, peer_id)
    return

@ffi.def_extern()
def read_cb(userdata, io_ptr, peer_id, packet_id, data_ptr, length):
    print("python: got data")
    data = ffi.buffer(data_ptr, length)
    protocol = ffi.from_handle(userdata)
    protocol.read(io_ptr, peer_id, packet_id, data)
    return

@ffi.def_extern()
def disconnected_cb(userdata, io_ptr, peer_id):
    print("python: disconnected")
    protocol = ffi.from_handle(userdata)
    protocol.disconnected(io_ptr, peer_id)
    return

"""Configuration for DevP2P Service"""
class Config(object):
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
    # Bootstrap nodes
    boot_nodes = [] # [string]

    """Obtain a pointer to configuration to use in Service.service call"""
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
