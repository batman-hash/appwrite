FROM node:18

WORKDIR /app

COPY . .

RUN if [ -f package.json ]; then npm install; fi

CMD ["node", "index.js"]
