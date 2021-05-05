setup:
	-brew install openssl
	python3 -m pip install geojson flask
	-pypy3 -m pip install geojson flask
	make -C backend
