#!/usr/bin/env python3
"""Watchdog P2P dla rejestratora GANZ NR8-32F84.

Odpytuje status P2P. Gdy rejestrator raportuje offline, wymusza ponowna
rejestracje przelaczajac flage enable (wylacz -> wlacz). Jest to znacznie
lzejsze niz restart urzadzenia i nie przerywa nagrywania.

O kazdej probie naprawy powiadamia przez Telegram. Zwykle przebiegi, gdy
wszystko dziala, nie generuja powiadomien.

Konfiguracja: /etc/nvr-p2p-watchdog.conf (klucz=wartosc, uprawnienia 0600).
Uzycie:
    watchdog.py                 normalny przebieg kontrolny
    watchdog.py --test-notify   wysyla testowe powiadomienie i konczy
"""
import configparser
import hashlib
import json
import logging
import logging.handlers
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Sciezki mozna nadpisac zmiennymi srodowiskowymi - przydatne przy testach.
CONFIG_PATH = os.environ.get("NVR_WATCHDOG_CONF", "/etc/nvr-p2p-watchdog.conf")
LOG_PATH = os.environ.get("NVR_WATCHDOG_LOG", "/var/log/nvr-p2p-watchdog.log")

# Ile sekund czekac, az rejestrator zdazy zarejestrowac sie po przelaczeniu.
# Obserwowany czas powrotu to ok. 90 s; 180 s daje zapas.
REREGISTER_WAIT = 180
# Przerwa miedzy wylaczeniem a ponownym wlaczeniem flagi.
TOGGLE_GAP = 15

log = logging.getLogger("p2p-watchdog")


class NvrError(Exception):
    pass


class Nvr:
    """Klient JSON-API rejestratora.

    Firmware wymaga surowego JSON-a w ciele zadania (bez URL-encodingu) oraz
    jednorazowego klucza, ktory serwer dokleja do kazdej odpowiedzi po
    znaczniku 'auth_key='. Klucz jest wazny dla jednego zadania.
    """

    def __init__(self, host, user, password, timeout=20):
        self.url = "http://%s/goform/WEB_JosnAjax" % host
        self.referer = "http://%s/asppage/base/login.html" % host
        self.user = user
        self.password = password
        self.timeout = timeout
        self._key = None

    def _post(self, payload, auth=None):
        body = "JsonReq=" + json.dumps(payload)
        if auth:
            body += "&subs_auth=" + json.dumps(auth)
        req = urllib.request.Request(
            self.url, data=body.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Referer": self.referer})
        raw = urllib.request.urlopen(req, timeout=self.timeout).read()
        return raw.decode("utf-8", "replace")

    def _parse(self, text):
        head, _, tail = text.partition("auth_key=")
        try:
            self._key = json.loads(tail)["key"]
        except (ValueError, KeyError):
            self._key = None
        try:
            return json.loads(head)
        except ValueError:
            raise NvrError("nieczytelna odpowiedz: %r" % head[:200])

    def call(self, cmd, data=None):
        if self._key is None:
            self._parse(self._post({"cmd": "get_login_key",
                                    "data": {"channel": 0}}))
        if self._key is None:
            raise NvrError("nie udalo sie pobrac klucza logowania")
        digest = hashlib.md5(
            (self.user + self._key + self.password).encode()).hexdigest()
        auth = {"subs": self.user, "prog": self._key, "enco": digest}
        payload = {"cmd": cmd}
        if data is not None:
            payload["data"] = data
        res = self._parse(self._post(payload, auth))
        if res.get("code") != 0:
            raise NvrError("%s zwrocilo code=%s" % (cmd, res.get("code")))
        return res

    def p2p_status(self):
        """Zwraca (enable, status). status: 1 = online, 0 = offline."""
        data = self.call("get_p2p_param", {"channel": 0}).get("data", {})
        return bool(data.get("enable")), int(data.get("status", 0))

    def set_p2p(self, enable):
        self.call("set_p2p_param", {"channel": 0, "enable": bool(enable)})


class Telegram:
    """Powiadomienia przez Bot API. Cisza, gdy nie skonfigurowano tokenu."""

    def __init__(self, token, chat_id, timeout=15):
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout

    @property
    def enabled(self):
        return bool(self.token and self.chat_id)

    def send(self, text):
        if not self.enabled:
            log.info("Telegram nieskonfigurowany - pomijam powiadomienie")
            return False
        url = "https://api.telegram.org/bot%s/sendMessage" % self.token
        body = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode()
        try:
            with urllib.request.urlopen(url, data=body,
                                        timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:200]
            log.error("Telegram HTTP %s: %s", exc.code, detail)
            return False
        except (urllib.error.URLError, OSError, ValueError) as exc:
            log.error("Telegram niedostepny: %s", exc)
            return False
        if not payload.get("ok"):
            log.error("Telegram odrzucil wiadomosc: %s", payload)
            return False
        log.info("powiadomienie Telegram wyslane")
        return True


def setup_logging():
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    try:
        handler = logging.handlers.RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=3)
    except OSError:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(fmt)
    log.addHandler(handler)
    # Druga kopia na stdout trafia do dziennika systemd.
    out = logging.StreamHandler(sys.stdout)
    out.setFormatter(fmt)
    log.addHandler(out)


def load_config():
    parser = configparser.ConfigParser()
    # Plik nie ma naglowka sekcji, wiec dokladamy go w locie.
    try:
        with open(CONFIG_PATH) as fh:
            parser.read_string("[nvr]\n" + fh.read())
    except OSError as exc:
        raise NvrError("nie mozna odczytac %s: %s" % (CONFIG_PATH, exc))
    s = parser["nvr"]
    return {
        "host": s.get("host", "192.168.50.200"),
        "user": s.get("user", "ADMIN"),
        "password": s.get("password", ""),
        "telegram_token": s.get("telegram_token", "").strip(),
        "telegram_chat_id": s.get("telegram_chat_id", "").strip(),
    }


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def main():
    setup_logging()
    try:
        cfg = load_config()
    except NvrError as exc:
        log.error("konfiguracja: %s", exc)
        return 2

    tg = Telegram(cfg["telegram_token"], cfg["telegram_chat_id"])
    where = socket.gethostname()

    if "--test-notify" in sys.argv:
        ok = tg.send(
            "Test watchdoga P2P\n\n"
            "Rejestrator: %s\n"
            "Wysylane z: %s\n"
            "Czas: %s\n\n"
            "Jesli widzisz te wiadomosc, powiadomienia dzialaja. "
            "Zwykle przebiegi kontrolne nie beda generowac powiadomien - "
            "wiadomosc dostaniesz tylko przy faktycznej awarii P2P."
            % (cfg["host"], where, stamp()))
        return 0 if ok else 1

    nvr = Nvr(cfg["host"], cfg["user"], cfg["password"])

    try:
        enable, status = nvr.p2p_status()
    except (NvrError, urllib.error.URLError, OSError) as exc:
        # Rejestrator bywa chwilowo niedostepny (jego warstwa uslug potrafi
        # zawiesic sie na kilka minut). To nie jest powod do przelaczania
        # ani do alarmowania - nastepny przebieg sprawdzi ponownie.
        log.warning("rejestrator nieosiagalny: %s", exc)
        return 1

    if not enable:
        log.warning("P2P jest wylaczony w konfiguracji - wlaczam")
        powod = "P2P bylo wylaczone w konfiguracji"
    elif status == 1:
        log.info("P2P online - bez zmian")
        return 0
    else:
        log.warning("P2P OFFLINE - wymuszam ponowna rejestracje")
        powod = "P2P zglaszalo status offline"

    try:
        nvr.set_p2p(False)
        time.sleep(TOGGLE_GAP)
        nvr.set_p2p(True)
    except (NvrError, urllib.error.URLError, OSError) as exc:
        log.error("przelaczenie nie powiodlo sie: %s", exc)
        tg.send("BLAD - watchdog P2P\n\n"
                "Rejestrator: %s\n"
                "Czas: %s\n\n"
                "%s, ale proba przelaczenia flagi nie powiodla sie:\n%s\n\n"
                "Prawdopodobnie potrzebny jest restart rejestratora."
                % (cfg["host"], stamp(), powod, exc))
        return 1

    log.info("flaga przelaczona, czekam %d s na rejestracje", REREGISTER_WAIT)
    start = time.time()
    deadline = start + REREGISTER_WAIT
    while time.time() < deadline:
        time.sleep(20)
        try:
            _, status = nvr.p2p_status()
        except (NvrError, urllib.error.URLError, OSError):
            continue
        if status == 1:
            trwalo = int(time.time() - start)
            log.info("P2P wrocilo online")
            tg.send("Watchdog P2P - naprawione\n\n"
                    "Rejestrator: %s\n"
                    "Czas: %s\n\n"
                    "%s. Wymuszono ponowna rejestracje i polaczenie wrocilo "
                    "po %d s.\n\nPodglad w aplikacji powinien dzialac."
                    % (cfg["host"], stamp(), powod, trwalo))
            return 0

    log.error("P2P nadal offline po %d s - moze byc potrzebny restart "
              "rejestratora", REREGISTER_WAIT)
    tg.send("UWAGA - watchdog P2P nie dal rady\n\n"
            "Rejestrator: %s\n"
            "Czas: %s\n\n"
            "%s. Przelaczenie flagi wykonano, ale po %d s status nadal jest "
            "offline.\n\nPrawdopodobnie potrzebny jest restart rejestratora."
            % (cfg["host"], stamp(), powod, REREGISTER_WAIT))
    return 1


if __name__ == "__main__":
    sys.exit(main())
