# Stage 1: Build wheel
FROM ghcr.io/prefix-dev/pixi:0.69.0-bookworm-slim AS builder

COPY pyproject.toml pixi.lock ./
RUN pixi install --locked -e workflow

# Copy source and git history after pixi install so that layer is cached until pixi.lock changes.
COPY src/workflow_app src/workflow_app/
COPY .git .git

RUN pixi run -e workflow wheel-workflow

# Stage 2: Runtime image
FROM ghcr.io/prefix-dev/pixi:0.69.0-bookworm-slim

COPY pixi.lock pyproject.toml ./
RUN pixi install --locked -e workflow

WORKDIR /usr/src/data_workflow

COPY --from=builder /src/workflow_app/dist/ ./dist/
RUN pixi run -e workflow pip install dist/*.whl && rm -rf dist/

COPY src/workflow_app/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
RUN chmod +x /usr/bin/docker-entrypoint.sh
CMD ["pixi", "run", "-e", "workflow", "/usr/bin/docker-entrypoint.sh"]
