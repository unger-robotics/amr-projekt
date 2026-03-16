# Netzwerkkonfiguration: iMac, MacBook, Raspberry Pi

## 1. Ausführung auf dem Raspberry Pi (amr.local)

Der Befehl ändert den Systemnamen dauerhaft auf `amr`.

```bash
# Hostnamen setzen
sudo hostnamectl set-hostname amr

```

## 2. Ausführung auf dem iMac (mac.local)

Der Block bereinigt alte Netzwerkeinträge, setzt den Systemnamen, schreibt die SSH-Konfiguration und verteilt die Authentifizierungsschlüssel an das MacBook und den Raspberry Pi.

*Hinweis: Der Befehl `ssh-copy-id` fordert während der Ausführung die jeweiligen Login-Passwörter der Zielgeräte an.*

```bash
# ----- Systemvorbereitung -----
sudo scutil --set ComputerName "mac"
sudo scutil --set LocalHostName "mac"
sudo scutil --set HostName "mac"
sudo sed -i '' '/amr/d' /etc/hosts

# ----- SSH-Basis-Konfiguration schreiben -----
mkdir -p ~/.ssh
cat << 'EOF' > ~/.ssh/config
# ----- Lokales Netzwerk -----
Host amr
    HostName amr.local
    User pi
    IdentityFile ~/.ssh/id_ed25519

Host book
    HostName book.local
    User jan
    # IdentityFile ~/.ssh/id_ed25519_macbook

# ----- Externe Dienste -----
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes

# ----- Globale Einstellungen -----
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
chmod 600 ~/.ssh/config

# ----- Schlüssel generieren und übertragen -----
# 1. Zum MacBook
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_macbook -N ""
ssh-copy-id -i ~/.ssh/id_ed25519_macbook.pub book
sed -i '' 's/# IdentityFile ~\/.ssh\/id_ed25519_macbook/IdentityFile ~\/.ssh\/id_ed25519_macbook/' ~/.ssh/config

# 2. Zum Raspberry Pi (Standard-Schlüssel nutzen)
ssh-copy-id -i ~/.ssh/id_ed25519.pub amr

```

## 3. Ausführung auf dem MacBook (book.local)

Der Block etabliert die Namensgebung und erzeugt gerätespezifische SSH-Schlüssel für die passwortlose Verbindung in Richtung des iMacs und des Raspberry Pis.

```bash
# ----- Systemvorbereitung -----
sudo scutil --set ComputerName "book"
sudo scutil --set LocalHostName "book"
sudo scutil --set HostName "book"

# ----- SSH-Basis-Konfiguration schreiben -----
mkdir -p ~/.ssh
cat << 'EOF' > ~/.ssh/config
# ----- Lokales Netzwerk -----
Host amr
    HostName amr.local
    User pi
    # IdentityFile ~/.ssh/id_ed25519_amr

Host mac
    HostName mac.local
    User jan
    # IdentityFile ~/.ssh/id_ed25519_imac

# ----- Globale Einstellungen -----
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
chmod 600 ~/.ssh/config

# ----- Schlüssel generieren und übertragen -----
# 1. Zum iMac
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_imac -N ""
ssh-copy-id -i ~/.ssh/id_ed25519_imac.pub mac
sed -i '' 's/# IdentityFile ~\/.ssh\/id_ed25519_imac/IdentityFile ~\/.ssh\/id_ed25519_imac/' ~/.ssh/config

# 2. Zum Raspberry Pi
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_amr -N ""
ssh-copy-id -i ~/.ssh/id_ed25519_amr.pub amr
sed -i '' 's/# IdentityFile ~\/.ssh\/id_ed25519_amr/IdentityFile ~\/.ssh\/id_ed25519_amr/' ~/.ssh/config

```

## 4. Erweiterte Netzwerk-Hierarchie (Raspberry Pi)

Dieser Abschnitt konfiguriert die Prioritäten der Funknetzwerke über den NetworkManager. Die kabelgebundene Ethernet-Schnittstelle (`eth0`) wird vom System standardmäßig über eine niedrigere Routing-Metrik priorisiert.

**Status und Routing prüfen:**
```bash
# Netzwerkumgebung aktualisieren
sudo nmcli device wifi rescan

# Auflistung der aktiven Systemkonfigurationen
nmcli connection show

# Routing-Tabelle und Metriken ausgeben (eth0 Metrik 100 > wlan0 Metrik 600)
ip route

```

**WLAN-Profile anlegen und priorisieren:**
Die Ausführung der folgenden Befehle erstellt die Profile und weist die hierarchischen Prioritätswerte (10, 5, 4) zu. *(Hinweis: Die Platzhalter `xxx` sind bei der initialen Ausführung durch die tatsächlichen WLAN-Passwörter zu ersetzen.)*

```bash
# Profil 1: iPhone-Hotspot (Hohe Priorität: 10)
sudo nmcli device wifi connect "iPhonej" password 'xxx' name "hotspot_profile"
sudo nmcli connection modify hotspot_profile connection.autoconnect-priority 10

# Profil 2: Heimnetzwerk 5 GHz (Mittlere Priorität: 5)
sudo nmcli device wifi connect "n5g" password 'xxx' name "n5g_profile"
sudo nmcli connection modify n5g_profile connection.autoconnect-priority 5

# Profil 3: Heimnetzwerk 2.4 GHz (Niedrige Priorität: 4)
sudo nmcli device wifi connect "n2g" password 'xxx' name "n2g_profile"
sudo nmcli connection modify n2g_profile connection.autoconnect-priority 4

```
