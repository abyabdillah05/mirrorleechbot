FROM arakurumi/mltb:heroku

WORKDIR /usr/src/app

RUN pip3 install curl_cffi
RUN pip3 install httpx[http2]

RUN chmod 777 /usr/src/app

COPY . .

CMD ["bash", "start.sh"]
