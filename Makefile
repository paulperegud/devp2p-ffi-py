.PHONY: test build

test: build
		python -m pytest tests/
	  python pinger.py

build: cffi_devp2p.so

cffi_devp2p.so: cffi_builder.py host.py libethcore_network.so
	  rm -f cffi_devp2p.{c,o,so}
		python cffi_builder.py

libethcore_network.so: ../devp2p/util/network/src/lib.rs
	(cd ../devp2p/util/network; make)
	cp ../devp2p/util/network/include/libethcore_network.h libethcore_network.h
	cp ../devp2p/util/network/target/debug/libethcore_network.so .
	sudo cp libethcore_network.h /usr/include/
	sudo cp libethcore_network.so /usr/local/lib/

clean:
	rm -f *.c *.a *.so *.h
	sudo rm -f /usr/include/libethcore_network.h
	sudo rm -f /usr/local/lib/libethcore_network.so

