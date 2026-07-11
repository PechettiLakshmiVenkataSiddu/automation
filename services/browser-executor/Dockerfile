FROM mcr.microsoft.com/playwright:v1.52.0-noble
WORKDIR /srv/browser-executor
COPY package.json ./
RUN npm install --omit=dev
COPY src ./src
USER pwuser
EXPOSE 8080
CMD ["node", "src/server.mjs"]
