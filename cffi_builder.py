import cffi

def _build_bindings():
    ffibuilder = cffi.FFI()
    ffibuilder.set_source("cffi_devp2p", '#include <libdevp2p_ffi.h>',
                          libraries=["devp2p_ffi"]
    )
    ffibuilder.cdef("""

    extern "Python+C" void initialize_cb(void*, void*);
    extern "Python+C" void connected_cb(void*, void*, size_t);
    extern "Python+C" void read_cb(void*, void*, size_t, uint8_t, uint8_t*, size_t);
    extern "Python+C" void disconnected_cb(void*, void*, size_t);

    typedef void (*InitializeCB)(void*, void*);
    typedef void (*ConnectedCB)(void*, void*, size_t);
    typedef void (*ReadCB)(void*, void*, size_t,
                           uint8_t, uint8_t*, size_t);
    typedef void (*DisconnectedCB)(void*, void*, size_t);

    struct StrLen {
        size_t len;
        char* buff;
    };

    struct Configuration {
        struct StrLen* config_path;
        struct StrLen* net_config_path;
        struct StrLen* listen_address;
        struct StrLen* public_address;
        uint16_t udp_port;
        struct StrLen* boot_node;
    };

    struct FFICallbacks {
        InitializeCB initialize;
        ConnectedCB connect;
        ReadCB read;
        DisconnectedCB disconnect;
    };

    void* config_local();
    void* config_with_port(uint16_t port);
    void* config_detailed(struct Configuration*, unsigned char* errno);

    void* network_service(void* config, unsigned char* errno);
    uint8_t network_service_start(void*);
    void network_service_free(void*);
    uint8_t network_service_add_protocol(void*,
                                         void*,
                                         char* protocol_id,
                                         uint8_t max_packet_id,
                                         char* versions,
                                         size_t versions_len,
                                         struct FFICallbacks* cbs
                                        );

    uint8_t peer_protocol_version(void* io,
                                  char* protocol_id,
                                  size_t peer, unsigned char* errno);
    void protocol_send(void* service, char* protocol_id,
                       size_t peer, uint8_t packet, char* buffer, size_t size);
    uint8_t protocol_reply(void* io, size_t peer, uint8_t packet, char* buffer, size_t size);

    uint8_t network_service_add_reserved_peer(void*, char*);
    char* network_service_node_name(void*);

    """)
    ffibuilder.compile()

if __name__ == "__main__":
    print "building bindings..."
    _build_bindings()
    print "building bindings... done!"
