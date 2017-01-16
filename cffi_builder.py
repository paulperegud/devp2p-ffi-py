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

    void* network_service(unsigned char* errno);
    uint8_t network_service_start(void*);
    void network_service_free(void*);
    uint8_t network_service_add_protocol(void*,
                                         void*,
                                         char* protocol_id,
                                         void (*initialize_cb)(void*, void*),
                                         void (*connected_cb)(void*, void*, size_t),
                                         void (*read_cb)(void*, void*, size_t,
                                                         uint8_t, uint8_t*, size_t),
                                         void (*disconnected_cb)(void*, void*, size_t)
                                        );

    uint8_t peer_protocol_version(void* io, size_t peer, unsigned char* errno);
    void protocol_send(void* service, char* protocol_id,
                       size_t peer, uint8_t packet, char* buffer, size_t size);
    void protocol_reply(void* io, size_t peer, uint8_t packet, char* buffer, size_t size);

    uint8_t network_service_add_reserved_peer(void*, char*);
    char* network_service_node_name(void*);

    """)
    ffibuilder.compile()

if __name__ == "__main__":
    print "building bindings..."
    _build_bindings()
    print "building bindings... done!"
