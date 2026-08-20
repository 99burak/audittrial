FROM node:22-alpine

WORKDIR /app

RUN chown node:node /app

COPY --chown=node:node package.json ./

USER node

RUN npm install

COPY --chown=node:node . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
