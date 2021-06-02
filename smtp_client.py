import json
import os
import socket
from base64 import b64encode
from ssl import wrap_socket

BOUNDARY = "----==--bound.8833.web38o.yandex.ru"
EXTENSION_TO_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/png",
    ".mp3": "audio/mpeg"
}


def load_settings():
    with open("./settings.json", "r") as f:
        return json.load(f)


def load_message_text():
    with open("./message/message.txt", 'r', encoding='cp1251') as f:
        text = f.read()

    if text[0] == '.':
        text = '.' + text

    return text.replace("\n.", "\n..")


def load_attachments():
    attachments = ''

    for filename in os.listdir(path="./message/attachments"):
        _, file_extension = os.path.splitext(filename)
        mime_type = EXTENSION_TO_MIME_TYPES[file_extension]

        with open(f"./message/attachments/{filename}", 'rb') as f:
            attachment = b64encode(f.read())
            attachments += (f'Content-Disposition: attachment; filename="{filename}"\n'
                            'Content-Transfer-Encoding: base64\n'
                            f'Content-Type: {mime_type}; name="{filename}"\n\n'
                            ) + attachment.decode() + f'\n--{BOUNDARY}'

    return attachments


def create_message(login, receivers, subject):
    return (
        f"From: {login}\n"
        f"To: {receivers}\n"
        f"Subject: {subject}\n"
        "MIME-Version: 1.0\n"
        f'Content-Type: multipart/mixed; boundary="{BOUNDARY}"\n\n'
        f"--{BOUNDARY}\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: 8bit\n\n"
        f"{load_message_text()}\n"
        f"--{BOUNDARY}\n"
        f"{load_attachments()}--\n."
    )


def send_request(sock, cmd, buffer_size=1024):
    sock.send(cmd + b'\n')
    return sock.recv(buffer_size).decode()


def main():
    settings = load_settings()
    login = settings["user"]["login"]
    password = settings["user"]["password"].encode()
    server_addr = (settings["server"]["host"], settings["server"]["port"])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock = wrap_socket(sock)
        sock.connect(server_addr)

        send_request(sock, b'EHLO test')

        send_request(sock, b'AUTH LOGIN')
        send_request(sock, b64encode(login.encode()))
        send_request(sock, b64encode(password))

        send_request(sock, b'MAIL FROM: ' + login.encode())

        receivers = input("Введите получаетелей через запятую\n")
        for receiver in receivers.split(","):
            send_request(sock, b'RCPT TO: ' + receiver.encode())

        subject = input("Введите тему\n")
        if not all(ord(i) < 128 for i in subject):
            subject = f'=?utf-8?B?{b64encode(subject.encode()).decode()}?='

        send_request(sock, b'DATA')
        send_request(sock, create_message(login, receivers, subject).encode())
        print("Сообщение отправлено")
        sock.recv(4096)


if __name__ == "__main__":
    main()
