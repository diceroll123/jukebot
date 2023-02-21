FROM docker.io/gorialis/discord.py:3.11.0-alpine-master-minimal

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "jukebot.py"]
