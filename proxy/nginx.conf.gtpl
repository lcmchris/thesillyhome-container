
server {
    listen 8099;

    server_name _;

    # Base Path für Ingress
    location / {
        proxy_pass {{ .server }};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket-Unterstützung
        proxy_set_header Sec-WebSocket-Protocol $http_sec_websocket_protocol;
        proxy_buffering off;
    }

    # CSS MIME-Type sicherstellen
    location ~* \.css$ {
        types {
            text/css css;
        }
        default_type text/css;
    }
}
