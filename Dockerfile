FROM ubuntu:20.04 as builder
WORKDIR /app
RUN apt update && apt install -y clang make libssl-dev python3.8 python3-pip  --no-install-recommends 
COPY . /app/viz
RUN make -C viz/backend && mkdir /app/.local && chown 10001:10001 /app/.local &&\
	mkdir /app/viz/.visualizefiles && chown 10001:10001 /app/viz/.visualizefiles
USER 10001
ENV HOME /app
RUN python3.8 -m pip install --user geojson flask

FROM ubuntu:20.04
WORKDIR /app
RUN apt update && apt install -y --no-install-recommends python3.8 && rm -rf /var/lib/apt/lists/*
EXPOSE 8000
USER 10001
ENV HOME /app
COPY --from=builder /app/ /app/
WORKDIR /app/viz
CMD ["python3.8", "/app/viz/visualize.py","sample/"]

