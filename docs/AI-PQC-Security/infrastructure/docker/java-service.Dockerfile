FROM maven:3.9.12-eclipse-temurin-21-alpine AS build

ARG MODULE
WORKDIR /workspace
COPY . .
RUN --mount=type=cache,target=/root/.m2 \
    mvn --batch-mode --no-transfer-progress -pl "${MODULE}" -am package -DskipTests

FROM eclipse-temurin:21-jre-alpine

ARG MODULE
ARG JAR_NAME
RUN addgroup -S app && adduser -S -G app app
WORKDIR /app
COPY --from=build "/workspace/${MODULE}/target/${JAR_NAME}" application.jar
USER app
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/application.jar"]
