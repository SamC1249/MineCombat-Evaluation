# syntax=docker/dockerfile:1

FROM eclipse-temurin:21-jdk AS plugin-build
WORKDIR /build
COPY paper-plugin/ ./paper-plugin/
RUN cd paper-plugin && chmod +x gradlew && ./gradlew jar --no-daemon

FROM eclipse-temurin:25-jdk AS runtime
WORKDIR /server

ARG PAPER_URL=https://fill-data.papermc.io/v1/objects/cfb9281c2657e21ecc8acdaa9efbd6b5b3e873fb5bac4c3b8ba4bba67aa13ee2/paper-26.1.2-65.jar

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o paper.jar "${PAPER_URL}"

COPY --from=plugin-build /build/paper-plugin/build/libs/minecombat-evaluation-0.1.0-SNAPSHOT.jar /server/plugins/
COPY paper-plugin/src/main/resources/config.yml /server/plugins/MineCombat-Evaluation/config.yml
COPY minecombat_eval/data/mcbench_flat-v1.zip /tmp/world.zip
RUN mkdir -p /server/mcbench_flat && unzip -q /tmp/world.zip -d /server/mcbench_flat && rm /tmp/world.zip

COPY server/server.properties.example /tmp/server.properties.example
RUN printf 'eula=true\nlevel-name=mcbench_flat\nlevel-type=minecraft:flat\nonline-mode=true\nmotd=MineCombat-Eval\n' > /server/server.properties

ENV EULA=TRUE
EXPOSE 25565 8765

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
