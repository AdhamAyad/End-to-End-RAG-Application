FROM node:20-alpine@sha256:8bda036ddd59ea51a23bc1a1035d3b5c614e72c01366d989f4120e8adca196d4 AS builder

WORKDIR /app

COPY package* .

RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine@sha256:4ff102c5d78d254a6f0da062b3cf39eaf07f01eec0927fd21e219d0af8bc0591

WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY --from=builder /app/dist .

COPY default.conf /etc/nginx/conf.d/default.conf

ARG ADMIN_CLOUD_RUN_URL
ENV ADMIN_CLOUD_RUN_URL=${ADMIN_CLOUD_RUN_URL}

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]