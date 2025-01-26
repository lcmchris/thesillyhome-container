
FROM nginx:alpine

# Tempio installieren (wird benötigt für die Template-Erstellung)
RUN apk add --no-cache bash curl jq && \
    curl -L https://github.com/home-assistant/tempio/releases/latest/download/tempio -o /usr/bin/tempio && \
    chmod +x /usr/bin/tempio

# Konfiguration und Einstiegspunkt hinzufügen
COPY nginx.conf.gtpl /nginx.conf.gtpl
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Standard-Port für NGINX
EXPOSE 8099

# Start des Proxies
ENTRYPOINT ["/entrypoint.sh"]
