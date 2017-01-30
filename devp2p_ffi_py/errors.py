class DevP2PException(Exception):
    pass

class DevP2PUnknownPeer(DevP2PException):
    pass
class DevP2PNetworkError(DevP2PException):
    pass

class DevP2PAuth(DevP2PNetworkError):
    pass
class DevP2PExpired(DevP2PNetworkError):
    pass
class DevP2PBadProtocol(DevP2PNetworkError):
    pass
class DevP2PPeerNotFound(DevP2PNetworkError):
    pass
class DevP2PDisconnected(DevP2PNetworkError):
    pass
class DevP2PUtil(DevP2PNetworkError):
    pass
class DevP2PIO(DevP2PNetworkError):
    pass
class DevP2PAddressParse(DevP2PNetworkError):
    pass
class DevP2PAddressResolve(DevP2PNetworkError):
    pass
class DevP2PStdIO(DevP2PNetworkError):
    pass

err_mapping = {
    255: DevP2PException,
    1: DevP2PUnknownPeer,
    2: DevP2PAuth,
    3: DevP2PExpired,
    4: DevP2PBadProtocol,
    5: DevP2PPeerNotFound,
    19: DevP2PDisconnected,
    29: DevP2PUtil,
    39: DevP2PIO,
    49: DevP2PAddressParse,
    59: DevP2PAddressResolve,
    69: DevP2PStdIO
}

def mb_raise_errno(code, msg = ""):
    if code != 0:
        raise_errno(code, msg)
    return code

def raise_errno(err, msg = ""):
    raise err_mapping[err](msg)
