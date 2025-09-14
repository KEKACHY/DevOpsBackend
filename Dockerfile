# Stage 1: Build the application
FROM node:lts-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install -g @quasar/cli && npm ci --ignore-scripts

COPY . .
RUN npx quasar prepare && quasar build

# Stage 2: Production
FROM nginx:stable-alpine

COPY --from=build-stage /app/dist/spa /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]