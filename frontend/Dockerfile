# 使用node為base Image
FROM node:14

# 設定為production環境
#ENV NODE_ENV production

# set up angular cli
RUN yarn global add @angular/cli@14.0.5

# 移動到工作用的dir
WORKDIR /app

# 將package.json 放入該資料夾內 (安裝依賴)
COPY package.json /app

# 安裝node_module
RUN npm install

# 把剩下的東西放入work_dir
COPY . /app

# create dist
RUN ng build

# expose 和 執行
#EXPOSE 4200
#CMD ["npm","start"]
