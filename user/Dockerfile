FROM node:14
EXPOSE 8080
WORKDIR /opt/server
COPY package.json .
COPY server.js .
RUN npm install
CMD ["node", "server.js"]


#user service require redis so we will directly install redis in roboshop network
# by using docker run -d --name redis --network=roboshop redis