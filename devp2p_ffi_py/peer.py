import time
import operator
from collections import OrderedDict

class UnknownCommandError(Exception):

    "raised if we receive an unknown command for a known protocol"
    pass

"""Peer represents a remote, connected host.
Helps to track version of devp2p protocol and set of subprotocols handled by
particular host. Because of the way FFI was build, it's more a collection of
connected subprotocols with the same host.
"""
class Peer(object):

    remote_client_version = ''
    protocols = {}
    peer_id = None
    _session_info = None # SessionInfo

    def __init__(self, peermanager, peer_id, remote_pubkey=None):
        self.protocols = OrderedDict()
        # log.debug('peer init', peer=self)

        self.peer_id = peer_id
        self.remote_pubkey = remote_pubkey

        # register p2p protocol
        # assert issubclass(self.peermanager.wire_protocol, P2PProtocol)
        # self.connect_service(self.peermanager)

    def __repr__(self):
        return "I am peer"
        # try:
        #     pn = self.connection.getpeername()
        # try:
        #     cv = '/'.join(self.remote_client_version.split('/')[:2])
        # except:
        #     cv = self.remote_client_version
        # return '<Peer%r %s>' % (pn, cv)

    def add_protocol(self, protocol):
        self.protocols[protocol.protocol_id] = protocol

    def rem_protocol(self, protocol):
        del self.protocols[protocol.protocol_id]

    def session_info(self):
        return self._session_info
        """Node ID and other data is in session.rs / SessionInfo"""
        raise NotImplemented()

    def report_error(self, reason):
        # try:
        #     ip_port = self.ip_port
        # except:
        #     ip_port = 'ip_port not available fixme'
        # self.peermanager.errors.add(ip_port, reason, self.remote_client_version)
        print "reporting error"

    # @property
    # def ip_port(self):
    #     try:
    #         return self.connection.getpeername()
    #     except Exception as e:
    #         log.debug('ip_port failed', e=e)
    #         raise e

    def connect_service(self, service):
        # assert isinstance(service, WiredService)
        # protocol_class = service.wire_protocol
        # assert issubclass(protocol_class, BaseProtocol)
        # create protcol instance which connects peer with serivce
        protocol = protocol_class(self, service)
        # # register protocol
        # assert protocol_class not in self.protocols
        # log.debug('registering protocol', protocol=protocol.name, peer=self)
        # self.protocols[protocol_class] = protocol
        # self.mux.add_protocol(protocol.protocol_id)
        protocol.start()

    def has_protocol(self, protocol):
        # assert issubclass(protocol, BaseProtocol)
        return protocol in self.protocols

    # sending p2p messages
    # do it via protocols

    # receiving p2p messages (from protocols)
    def receive(packet, packet_id, protocol_id):
        raise NotImplemented()
