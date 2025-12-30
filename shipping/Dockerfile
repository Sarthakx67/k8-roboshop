FROM maven AS build

WORKDIR /opt/shipping

COPY pom.xml .
RUN mvn dependency:resolve
COPY src ./src
RUN mvn package

# Run
FROM eclipse-temurin:8-jre-alpine

EXPOSE 8080
WORKDIR /opt/shipping

COPY --from=build /opt/shipping/target/shipping-1.0.jar shipping.jar
CMD ["java", "-Xmn256m", "-Xmx768m", "-jar", "shipping.jar"]