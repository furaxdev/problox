FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.aftman/bin:${PATH}"

WORKDIR /workspace
COPY . /workspace

RUN chmod +x scripts/setup_sandbox.sh

# Les outils Roblox (Aftman/Rojo/Selene/StyLua/Wally) et les deps Python sont
# installés au premier `docker run` via scripts/setup_sandbox.sh plutôt qu'au
# build, pour ne pas figer des versions dans l'image et garder le download
# auditable/rejouable dans le sandbox.

CMD ["/bin/bash"]
