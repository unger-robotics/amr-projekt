#!/bin/bash

# Parameter-Definition
TARGET_HOST=${1:-"amr"}
SSH_USER=${2:-"pi"}
PI_OUIS="2c:cf:67|d8:3a:dd|b8:27:eb|dc:a6:32|e4:5f:0?1|28:cd:c1|88:a2:9e|8c:1f:64|f0:40:af"

# Funktion zur isolierten mDNS-Prüfung
check_mdns() {
    local PING_OUT
    PING_OUT=$(ping -c 1 -t 1 "${TARGET_HOST}.local" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$PING_OUT" | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -n 1
    fi
}

echo "Suche nach Host '${TARGET_HOST}.local' im Netzwerk..."

# 1. mDNS-Auflösung (Erster Versuch)
MDNS_IP=$(check_mdns)

if [ -n "$MDNS_IP" ]; then
    echo "Erfolg: Host via mDNS erreichbar unter $MDNS_IP"
    exec ssh "${SSH_USER}@${MDNS_IP}"
fi

# 2. mDNS-Auflösung (Zweiter Versuch nach Wartezeit)
echo "Initiale mDNS-Suche erfolglos. Warte 10 Sekunden auf möglichen Netzwerkwechsel der Ziel-Hardware..."
sleep 10
MDNS_IP=$(check_mdns)

if [ -n "$MDNS_IP" ]; then
    echo "Erfolg: Host nach Wartezeit via mDNS erreichbar unter $MDNS_IP"
    exec ssh "${SSH_USER}@${MDNS_IP}"
fi

echo "mDNS-Ziel final nicht erreichbar. Starte dynamischen ARP-Subnetz-Scan auf allen aktiven IPv4-Schnittstellen..."

# 3. Mathematische Hilfsfunktionen für 32-Bit-Integer-Konvertierung
ip_to_int() {
    local a b c d
    IFS=. read -r a b c d <<< "$1"
    echo $(( (a << 24) + (b << 16) + (c << 8) + d ))
}

int_to_ip() {
    local ui32=$1
    echo "$(( (ui32 >> 24) & 255 )).$(( (ui32 >> 16) & 255 )).$(( (ui32 >> 8) & 255 )).$(( ui32 & 255 ))"
}

# 4. Multi-Interface-Loop (mit universeller IP-Ermittlung via ifconfig)
INTERFACES=$(ifconfig -l)
PI_FOUND_IP=""

for INTERFACE in $INTERFACES; do
    IFCONFIG_OUT=$(ifconfig "$INTERFACE" 2>/dev/null | grep 'inet ' | head -n 1)
    MY_IP=$(echo "$IFCONFIG_OUT" | awk '{print $2}')
    SUBNET_HEX=$(echo "$IFCONFIG_OUT" | awk '{print $4}')

    if [ -n "$MY_IP" ] && [ -n "$SUBNET_HEX" ] && [[ "$SUBNET_HEX" == 0x* ]]; then

        if [ "$MY_IP" = "127.0.0.1" ]; then
            continue
        fi

        SUBNET_MASK=$((16#${SUBNET_HEX:2:2})).$((16#${SUBNET_HEX:4:2})).$((16#${SUBNET_HEX:6:2})).$((16#${SUBNET_HEX:8:2}))

        echo "Prüfe Schnittstelle $INTERFACE (IP: $MY_IP, Maske: $SUBNET_MASK)..."

        IP_INT=$(ip_to_int "$MY_IP")
        MASK_INT=$(ip_to_int "$SUBNET_MASK")

        NETWORK_INT=$(( IP_INT & MASK_INT ))
        BROADCAST_INT=$(( NETWORK_INT | ~MASK_INT & 0xFFFFFFFF ))

        START_IP=$(( NETWORK_INT + 1 ))
        END_IP=$(( BROADCAST_INT - 1 ))

        echo "  Scanne Adressbereich $(int_to_ip "$START_IP") bis $(int_to_ip "$END_IP")..."

        for (( i=START_IP; i<=END_IP; i++ )); do
            ping -c 1 -t 1 "$(int_to_ip "$i")" >/dev/null 2>&1 &
        done
        wait

        ARP_IPS=$(arp -a | grep -iE "$PI_OUIS" | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}')

        for ARP_IP in $ARP_IPS; do
            ping -c 1 -t 1 "$ARP_IP" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                PI_FOUND_IP="$ARP_IP"
                break 2
            else
                echo "  Ignoriere veralteten oder unerreichbaren ARP-Eintrag: $ARP_IP"
            fi
        done
    fi
done

# 5. SSH-Aufruf oder Abbruch
if [ -n "$PI_FOUND_IP" ]; then
    echo "Erfolg: Hardware verifiziert und gefunden unter $PI_FOUND_IP"
    exec ssh "${SSH_USER}@${PI_FOUND_IP}"
else
    echo "Fehler: Keine erreichbare Raspberry Pi MAC-Adresse in den aktiven IPv4-Subnetzen gefunden."
    exit 1
fi
