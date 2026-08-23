# Voice Command Shopping Assistant — single-stage build.
# The C++ server (cpp-httplib + ONNX Runtime) serves both the API and the
# static frontend on one port, so the image needs no Python at runtime.
FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ make ca-certificates locales && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

WORKDIR /app

# Server source + vendored deps (onnxruntime prebuilt libs, header-only
# cpp-httplib and nlohmann/json — see server/README section on third_party/)
COPY server/ /app/server/

WORKDIR /app/server
RUN make

# Runtime data: trained model + dictionaries, and the static frontend.
# (already copied via `server/` above: server/data and server/public)

ENV PORT=8080
EXPOSE 8080

# Make the vendored onnxruntime shared lib discoverable at runtime.
ENV LD_LIBRARY_PATH=/app/server/third_party/onnxruntime/lib

CMD ["./vsa-server", "--data-dir", "data", "--static-dir", "public"]
