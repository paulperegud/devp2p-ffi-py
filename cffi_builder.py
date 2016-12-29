import cffi

def _build_bindings():
    ffibuilder = cffi.FFI()
    ffibuilder.set_source("cffi_devp2p", '#include <libethcore_network.h>',
                          libraries=["ethcore_network"]
    )
    ffibuilder.cdef("""

    int32_t add_five(int32_t x);
    int32_t say_hello(int(*callback)(int));
    extern "Python+C" int hello_python(int);
    extern "Python+C" void connected(void*, void*, int32_t);

    void* network_service();
    uint8_t network_service__start(void*);
    void network_service__free(void*);
    uint8_t network_service__add_protocol(void*);
    uint8_t network_service__add_reserved_peer(void*, char*);
    char* network_service__node_name(void*);
    int32_t network_service__read_number(void*);

    """)
    ffibuilder.compile()

    # int32_t say_hello(void(*callback)(int));
    # extern "Python+C" void hello_python(int);
    # char* hello_rust();
    # int32_t new_network_service(int);
    # int32_t add_five(int32_t x);


if __name__ == "__main__":
    print "building bindings..."
    _build_bindings()
    print "building bindings... done!"
