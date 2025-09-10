FROM node:20-alpine

RUN apk add --no-cache python3 py3-pip py3-setuptools

RUN pip3 install --break-system-packages uv

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]