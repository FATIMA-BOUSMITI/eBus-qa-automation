FROM maven:3.9-eclipse-temurin-17
RUN curl -fsSL https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz -o /tmp/jmeter.tgz \
 && curl -fsSL https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz.sha512 -o /tmp/jmeter.sha512 \
 && expected=$(grep -Eo '[[:xdigit:]]{128}' /tmp/jmeter.sha512 | head -n 1) \
 && test -n "$expected" \
 && printf '%s  %s\n' "$expected" /tmp/jmeter.tgz | sha512sum -c - \
 && tar -xzf /tmp/jmeter.tgz -C /opt
WORKDIR /workspace
RUN test -s /opt/apache-jmeter-5.6.3/lib/slf4j-api-1.7.36.jar \
 && /opt/apache-jmeter-5.6.3/bin/jmeter --version > /tmp/jmeter-version.txt
ENTRYPOINT ["/opt/apache-jmeter-5.6.3/bin/jmeter"]
