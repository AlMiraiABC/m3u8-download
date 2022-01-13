FROM python:3.8.12-alpine
LABEL version="1.0"
LABEL author="almirai"
LABEL maintainer="live.almirai@outlook.com"
WORKDIR /root
COPY . .
VOLUME [ "./ts", "./tmp", "./log", "./downloaded", "./m3u8" ]
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
CMD python3 main.py
