# Offline inset replay (Python tooling only)
#
# Purpose: one-command regeneration of committed results/ tables from frozen
# fixtures and logs, which is what a reviewer typically tries first.
#
# NOT in scope: eBPF verifier behavior. Containers share the host kernel;
# clang/bpftool/lab capture are separate from this image. Do not treat this
# Dockerfile as answering multi-kernel portability.

FROM python:3.12-slim-bookworm

WORKDIR /src
COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY bpfix_adversarial ./bpfix_adversarial
COPY tools ./tools
COPY tests ./tests
COPY fixtures ./fixtures
COPY mutants ./mutants
COPY campaigns ./campaigns
COPY results ./results
COPY figures ./figures
COPY schemas ./schemas
COPY docs ./docs
COPY Makefile ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r requirements.txt

# Default: smoke + verify that every committed results/ table and figure equals
# a fresh emitter run (fails on drift). `make insets` would regenerate and
# overwrite results/ silently, so it cannot detect drift.
CMD ["bash", "-lc", "make smoke && python tools/check_results_fresh.py"]
