# Build the Vite app, then serve the static bundle with a tiny static server.
FROM node:20-alpine AS build
WORKDIR /app
# Baked into the static bundle so the browser calls the backend directly.
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist
EXPOSE 5173
# SPA fallback so client-side routes resolve.
CMD ["serve", "-s", "dist", "-l", "5173"]
