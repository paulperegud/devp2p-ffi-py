.PHONY: test build

test: build
		python -m pytest tests/

build: cffi_devp2p.so

cffi_devp2p.so: cffi_builder.py host.py libdevp2p_ffi.so
	  rm -f cffi_devp2p.{c,o,so}
		python cffi_builder.py

libdevp2p_ffi.so: ../devp2p-ffi/src/lib.rs ../devp2p-ffi/include/libdevp2p_ffi.h
	(cd ../devp2p-ffi/; cargo build)
	cp ../devp2p-ffi/include/libdevp2p_ffi.h .
	cp ../devp2p-ffi/target/debug/libdevp2p_ffi.so .
	sudo cp libdevp2p_ffi.h /usr/include/
	sudo cp libdevp2p_ffi.so /usr/lib/
	sudo cp libdevp2p_ffi.so /usr/local/lib/


clean:
	rm -f *.c *.a *.so *.h *.o
	sudo rm /usr/include/libdevp2p_ffi.h
	sudo rm /usr/lib/libdevp2p_ffi.so

# TODO for later:
# automate building system using CI (via github)
# Build static files
