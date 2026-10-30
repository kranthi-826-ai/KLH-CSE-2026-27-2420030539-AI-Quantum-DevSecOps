FROM node:24-alpine AS build
WORKDIR /app
COPY frontend/web-dashboard/package*.json ./
RUN npm ci
COPY frontend/web-dashboard/ ./
RUN npm run build

FROM nginx:1.29-alpine
RUN apk upgrade --no-cache
COPY frontend/web-dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
