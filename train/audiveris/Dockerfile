# Audiveris OMR engine.
# Built on the prebuilt `toprock/audiveris` image (Audiveris 5.x + JRE), which
# installs the binary at /audiveris-extract/bin/Audiveris.
FROM toprock/audiveris:latest

COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh

# Args: <input_file> <output_dir>  (paths inside the container, under /data)
ENTRYPOINT ["/entrypoint.sh"]
