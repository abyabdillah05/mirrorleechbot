FROM pikachuproject/mltbpika:beta

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY . .

RUN pip install --break-system-packages --ignore-installed --force-reinstall -r requirements.txt

CMD ["bash", "start.sh"]