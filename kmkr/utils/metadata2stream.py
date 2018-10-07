
import time
import requests

icecast_username = "env"
icecast_password = "env"
icecast_host = "env"
icecast_port = "env"
icecast_mount = "env"  # don't include leading slash

icecast_url_pattern = "http://{}:{}/admin/metadata?mount=/{}&mode=updinfo&song=".format(
    icecast_host, icecast_port, icecast_mount)


def get_now_playing() -> str:
    return "KMKR"


def update_icecast(meta: str):
    if meta != '':
        print(meta)
        meta_fmt = meta.replace(" ", "+")  # add "+" instead of " " for icecast2
        url = icecast_url_pattern.format(meta_fmt)
        r = requests.get(url, auth=(icecast_username, icecast_password))
        status = r.status_code
        now_gmt = time.gmtime()
        timestamp = time.asctime(now_gmt)
        print(timestamp)

        if status == 200:
            print("Icecast Update OK")
        else:
            print("Icecast Update Error", status)


while True:  # infinite loop
    meta = get_now_playing()
    update_icecast(meta)
    time.sleep(1)  # pause
