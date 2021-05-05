lib/libvis.so: include/csvmonkey.hpp \
	src/main.cpp src/stop_times_loader.h src/gtfs_files.h src/routes_loader.h src/trips_loader.h \
	src/sjson.h 
	c++ -g -Wunused -Wall -Wextra -shared -rdynamic -fPIC -lcrypto -L/usr/local/opt/openssl/lib -I/usr/local/opt/openssl/include -Iinclude -msse4.2 -O3 -std=c++17 src/main.cpp -o lib/libvis.so

