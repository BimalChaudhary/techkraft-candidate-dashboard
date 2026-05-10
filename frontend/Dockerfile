FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api

CMD ["npm", "run", "dev", "--", "-p", "3000"]
