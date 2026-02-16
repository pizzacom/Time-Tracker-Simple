FROM nginx:1.25-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files
COPY index.html /usr/share/nginx/html/
COPY login.html /usr/share/nginx/html/
COPY manifest.json /usr/share/nginx/html/
COPY sw.js /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY icons/ /usr/share/nginx/html/icons/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
