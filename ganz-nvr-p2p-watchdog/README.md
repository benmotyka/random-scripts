# Watchdog P2P dla rejestratora GANZ NR8-32F84

Automatycznie przywraca połączenie P2P, gdy rejestrator przestaje być widoczny
w aplikacji mobilnej. Powiadamia przez Telegram o każdej naprawie.

---

## Problem

Raz na jakiś czas — obserwowany rytm to mniej więcej raz w tygodniu — podgląd
kamer z sieci zewnętrznej przestaje działać. W panelu rejestratora funkcja P2P
jest włączona, ale jej status to **offline**. Dostęp lokalny po adresie IP
działa przez cały czas bez zarzutu. Restart rejestratora czasem pomaga, czasem
nie.

### Co zostało wykluczone

Producent wskazywał na blokadę portów UDP 31000 i TCP 3800 po stronie routera.
Test STUN z tej samej sieci pokazał jednak, że sieć jest w pełni sprawna:

```
ten sam port lokalny → trzy różne serwery STUN
  stun.l.google.com    → 188.191.207.xx:61617
  stun1.l.google.com   → 188.191.207.xx:61617
  stun.cloudflare.com  → 188.191.207.xx:61617
```

Identyczne mapowanie niezależnie od celu oraz zachowanie numerów portów
oznaczają **NAT typu cone** (nie symetryczny), publiczny adres IP (nie CGNAT)
i brak filtrowania ruchu wychodzącego UDP. Hole punching działa.

Wykluczone również: martwy serwer DNS (osobna usterka, naprawiona wcześniej),
brama domyślna, konflikt adresów IP w sieci lokalnej.

### Przyczyna faktyczna

Przełączenie samej flagi `enable` w ustawieniach P2P — **bez restartu
urządzenia i bez żadnej zmiany w sieci** — przywraca status online w około
90 sekund.

Gdyby blokował router, operator albo DNS, przełącznik nic by nie dał. Wniosek:
klient P2P w firmware zawiesza się i nie ponawia rejestracji na serwerze
producenta. To błąd oprogramowania rejestratora, nie konfiguracji sieci.

Wersja firmware, na której zdiagnozowano problem: `v4.5.0832.0000.130.0.1.39.3`.

---

## Rozwiązanie

Skrypt uruchamiany co 30 minut przez timer systemd:

1. odpytuje status P2P przez API rejestratora,
2. gdy status to **online** — zapisuje wiersz w logu i kończy pracę,
3. gdy status to **offline** — wyłącza flagę `enable`, czeka 15 sekund,
   włącza ją z powrotem, a następnie przez maksymalnie 3 minuty sprawdza,
   czy połączenie wróciło,
4. wysyła powiadomienie Telegram z wynikiem naprawy.

Przełączenie flagi jest znacznie lżejsze niż restart urządzenia — trwa
sekundy i **nie przerywa nagrywania**.

### Zachowanie przy niedostępnym rejestratorze

Warstwa usług tego firmware potrafi się zawiesić na kilka minut — przestają
odpowiadać wszystkie porty TCP, choć ICMP nadal działa. W takiej sytuacji
skrypt **nie przełącza niczego** i nie wysyła alarmu, tylko notuje ostrzeżenie
w logu i czeka na kolejny przebieg.

---

## Instalacja

```bash
git clone <repo> && cd ganz-nvr-p2p-watchdog
sudo ./install.sh
sudo nano /etc/nvr-p2p-watchdog.conf   # uzupełnij hasło i dane bota
sudo /opt/nvr-p2p-watchdog/watchdog.py --test-notify
```

Wymagania: Python 3 z biblioteki standardowej (bez zewnętrznych zależności),
systemd, dostęp sieciowy do rejestratora.

Instalator jest idempotentny — istniejącej konfiguracji nie nadpisuje.

### Co gdzie ląduje

| Ścieżka | Uprawnienia | Zawartość |
|---|---|---|
| `/opt/nvr-p2p-watchdog/watchdog.py` | `755 root:root` | skrypt |
| `/etc/nvr-p2p-watchdog.conf` | `600 root:root` | hasło i token bota |
| `/etc/systemd/system/nvr-p2p-watchdog.{service,timer}` | `644 root:root` | jednostki |
| `/var/log/nvr-p2p-watchdog.log` | | log z rotacją, 4 × 1 MB |

---

## Konfiguracja

Wzorzec w `nvr-p2p-watchdog.conf.example`.

| Klucz | Opis |
|---|---|
| `host` | adres rejestratora w sieci lokalnej |
| `user` | login do panelu — **wielkimi literami**, patrz uwaga niżej |
| `password` | hasło do panelu |
| `telegram_token` | token bota od `@BotFather`; puste = powiadomienia wyłączone |
| `telegram_chat_id` | identyfikator czatu, np. od `@userinfobot` |

Timer chodzi co 30 minut (`OnUnitActiveSec`), startuje 5 minut po
uruchomieniu systemu i dzięki `Persistent=true` nadrabia przebiegi pominięte,
gdy urządzenie było wyłączone. Częstotliwość zmienisz w
`systemd/nvr-p2p-watchdog.timer`, po czym `sudo systemctl daemon-reload`.

---

## Powiadomienia

Wiadomość przychodzi **wyłącznie przy faktycznej awarii** — zwykłe przebiegi
kontrolne milczą, więc przy jednej awarii tygodniowo to jedna wiadomość
tygodniowo, a nie 48 dziennie.

Trzy rodzaje:

- **naprawione** — wykryto offline, przełączono flagę, połączenie wróciło
  (z podaniem, ile to trwało),
- **nie dało rady** — przełączenie wykonano, ale po 3 minutach status nadal
  offline; prawdopodobnie potrzebny restart rejestratora,
- **błąd** — samo przełączenie flagi się nie powiodło.

Test: `sudo /opt/nvr-p2p-watchdog/watchdog.py --test-notify`

---

## Obsługa

```bash
sudo tail -f /var/log/nvr-p2p-watchdog.log      # podgląd na żywo
systemctl list-timers nvr-p2p-watchdog          # kiedy następny przebieg
sudo systemctl start nvr-p2p-watchdog.service   # uruchom natychmiast
journalctl -u nvr-p2p-watchdog.service          # historia w dzienniku systemd
sudo systemctl disable --now nvr-p2p-watchdog.timer   # wyłącz
```

Przykładowy log z rzeczywistej naprawy:

```
17:06:05  WARNING  P2P jest wylaczony w konfiguracji - wlaczam
17:06:20  INFO     flaga przelaczona, czekam 180 s na rejestracje
17:07:55  INFO     P2P wrocilo online
17:36:16  INFO     P2P online - bez zmian
```

---

## API rejestratora — pułapki

Notatki z inżynierii wstecznej panelu WWW. Przydatne przy rozbudowie skryptu.

**Endpoint:** `POST http://<host>/goform/WEB_JosnAjax`,
ciało `JsonReq={...}&subs_auth={...}` jako `x-www-form-urlencoded`.

1. **JSON musi być surowy, bez URL-encodingu.** Oryginalny `Ajax.js` skleja
   parametry ręcznie i nie enkoduje wartości. Poprawnie zaenkodowane żądanie
   zwraca pustą odpowiedź.
2. **Klucz jest jednorazowy.** Serwer dokleja go do *każdej* odpowiedzi po
   znaczniku `auth_key=`. Odpowiedź trzeba rozdzielić na JSON i klucz, a klucz
   zapamiętać na następne żądanie.
3. **Uwierzytelnianie:** `enco = md5(login + klucz + hasło)`, login wielkimi
   literami (`ADMIN`, nie `admin`).
4. **Brak wymaganego parametru wysypuje cały serwer.** Padają wszystkie usługi
   TCP — panel, protokół prywatny, RTSP. ICMP nadal odpowiada. Powrót trwa
   około 5 minut. Nie testuj komend na ślepo.
5. **Format dat w logach:** `YYYY/MM/DD HH:MM:SS`. Myślniki powodują awarię
   z punktu 4.

Użyte komendy:

| Komenda | Parametry |
|---|---|
| `get_login_key` | `{channel:0}`, bez `subs_auth` |
| `get_p2p_param` | `{channel:0}` → `status`: **1 = online, 0 = offline** |
| `set_p2p_param` | `{channel:0, enable:bool}` |

Mapa pozostałych podstron panelu: `http://<host>/config/setting.json`,
moduły JS: `http://<host>/js/dynamic/<nazwa>.js`.

---

## Bezpieczeństwo

Plik `/etc/nvr-p2p-watchdog.conf` zawiera hasło do monitoringu i token bota.
Uprawnienia `600 root:root`. `.gitignore` blokuje przypadkowe zacommitowanie
wypełnionej wersji — w repozytorium trzymamy wyłącznie `.example`.

---

## Uwagi

Watchdog jest **obejściem, nie naprawą**. Właściwym rozwiązaniem jest poprawka
firmware. Log gromadzi statystykę częstotliwości awarii, co stanowi konkretny
materiał do zgłoszenia u producenta:

> Przełączenie samej flagi „Enable P2P" — bez restartu urządzenia i bez zmian
> po stronie sieci — przywróciło status z offline na online w ciągu 90 sekund.
> Test STUN potwierdza NAT typu cone z zachowaniem portów oraz publiczny adres
> IP; ruch wychodzący nie jest blokowany. Problem leży w mechanizmie ponownej
> rejestracji P2P w firmware, nie w konfiguracji sieci.
