# Claude Code auf Raspberry Pi 5 installieren

## 1. Voraussetzungen pruefen

```bash
# Muss "aarch64" ausgeben (nicht armv7l)
uname -m

# Pi 5 hat standardmaessig 4+ GB RAM - passt
```

Falls `armv7l` kommt: 64-Bit Raspberry Pi OS neu flashen.

## 2. System aktualisieren

```bash
sudo apt update && sudo apt upgrade
```

## 3. Claude Code installieren

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Das ist der empfohlene Weg (nativer Installer). Die alte npm-Methode (`npm install -g @anthropic-ai/claude-code`) ist deprecated.

## 4. Authentifizieren und starten

```bash
claude
```

Beim ersten Start wirst du nach Anmeldedaten gefragt. Du brauchst entweder:
- Ein **Claude Pro/Max/Team-Abo**, oder
- Einen **Anthropic Console API-Key** mit aktivem Billing

## 5. Installation pruefen

```bash
claude doctor
```

## Bekannte Stolpersteine

- **Architektur-Erkennung**: In Version 1.0.51 gab es einen Bug, der ARM64 faelschlicherweise als 32-Bit erkannte. In aktuellen Versionen behoben.
- **npm-Permissions**: Falls du doch npm nutzt, **niemals** `sudo npm install -g` verwenden. Stattdessen npm-Prefix auf Home setzen:
  ```bash
  mkdir ~/.npm-global
  npm config set prefix '~/.npm-global'
  echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
  ```

Installationsdauer auf dem Pi 5: ca. 15-30 Minuten bei guter Netzverbindung.
