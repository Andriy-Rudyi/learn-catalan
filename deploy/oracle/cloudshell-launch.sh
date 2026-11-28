#!/bin/bash
# Create the site's server in Oracle Cloud as soon as there is room for it.
#
# Run in Cloud Shell (the >_ icon at the top right of the Oracle console):
#
#   curl -fsSL https://raw.githubusercontent.com/Andriy-Rudyi/learn-catalan/dev/deploy/oracle/cloudshell-launch.sh -o launch.sh
#   bash launch.sh check     # is there room right now? (creates nothing)
#   bash launch.sh           # try every 2 minutes until a server is created
#
# Needs the network made by the VCN wizard, named "langsite-vcn". It tries,
# in this order: Ampere 2 OCPU / 12 GB, Ampere 1 OCPU / 6 GB, the small AMD
# server (all Always Free). The new server runs deploy/oracle/setup.sh on
# its first boot. Its SSH key is made here, in ~/.ssh/langsite; at the end
# the script prints what goes into the GitHub secrets ORACLE_HOST and
# ORACLE_SSH_KEY. Cloud Shell closes after a while without activity: just
# run it again, it picks up where it was.
set -uo pipefail

T="${OCI_TENANCY:?Run this in Oracle Cloud Shell}"
NAME=langsite
INIT='#!/bin/bash
curl -fsSL https://raw.githubusercontent.com/Andriy-Rudyi/learn-catalan/dev/deploy/oracle/setup.sh | bash'

AD=$(oci iam availability-domain list --compartment-id "$T" --query 'data[0].name' --raw-output)
echo "Availability domain: $AD"

# Each try: shape, its settings, disk size (GB).
TRIES=(
  'VM.Standard.A1.Flex|{"ocpus":2,"memoryInGBs":12}|100'
  'VM.Standard.A1.Flex|{"ocpus":1,"memoryInGBs":6}|100'
  'VM.Standard.E2.1.Micro||50'
)

capacity() {  # shape, settings -> AVAILABLE / OUT_OF_HOST_CAPACITY / ...
  local item="{\"instanceShape\":\"$1\""
  [ -n "$2" ] && item="$item,\"instanceShapeConfig\":$2"
  item="$item}"
  oci compute compute-capacity-report create --compartment-id "$T" --availability-domain "$AD" \
    --shape-availabilities "[$item]" \
    --query 'data."shape-availabilities"[0]."availability-status"' --raw-output 2>/dev/null || echo UNKNOWN
}

if [ "${1:-}" = check ]; then
  for try in "${TRIES[@]}"; do
    IFS='|' read -r shape config _disk <<< "$try"
    echo "$shape ${config:-}: $(capacity "$shape" "$config")"
  done
  exit 0
fi

existing=$(oci compute instance list --compartment-id "$T" --display-name "$NAME" \
  --lifecycle-state RUNNING --query 'data[0].id' --raw-output 2>/dev/null)
if [ -n "$existing" ] && [ "$existing" != null ]; then
  echo "A server named $NAME is already running."
  instance="$existing"
else
  vcn=$(oci network vcn list --compartment-id "$T" --display-name langsite-vcn --query 'data[0].id' --raw-output)
  if [ -z "$vcn" ] || [ "$vcn" = null ]; then
    echo "No network named langsite-vcn: create it with the VCN wizard first." >&2; exit 1
  fi
  subnet=$(oci network subnet list --compartment-id "$T" --vcn-id "$vcn" \
    --query 'data[?"prohibit-public-ip-on-vnic"==`false`] | [0].id' --raw-output)
  if [ -z "$subnet" ] || [ "$subnet" = null ]; then
    echo "langsite-vcn has no public subnet." >&2; exit 1
  fi

  mkdir -p ~/.ssh
  # RSA: Cloud Shell runs in FIPS mode, which refuses ED25519 keys.
  [ -f ~/.ssh/langsite.pub ] || { rm -f ~/.ssh/langsite; ssh-keygen -t rsa -b 4096 -m PEM -N '' -C langsite -f ~/.ssh/langsite -q; }
  if [ ! -f ~/.ssh/langsite.pub ]; then
    echo "Could not make the SSH key ~/.ssh/langsite." >&2; exit 1
  fi
  printf '%s\n' "$INIT" > ~/langsite-init.sh

  declare -A images=()  # the newest Ubuntu 24.04 image for each shape
  instance=""
  round=0
  while [ -z "$instance" ]; do
    round=$((round + 1))
    for try in "${TRIES[@]}"; do
      IFS='|' read -r shape config disk <<< "$try"
      if [ -z "${images[$shape]:-}" ]; then
        images[$shape]=$(oci compute image list --compartment-id "$T" --operating-system "Canonical Ubuntu" \
          --operating-system-version "24.04" --shape "$shape" --sort-by TIMECREATED --sort-order DESC \
          --query 'data[0].id' --raw-output)
      fi
      image="${images[$shape]}"
      args=(--compartment-id "$T" --availability-domain "$AD" --shape "$shape" --image-id "$image"
            --subnet-id "$subnet" --assign-public-ip true --display-name "$NAME"
            --ssh-authorized-keys-file ~/.ssh/langsite.pub --user-data-file ~/langsite-init.sh
            --boot-volume-size-in-gbs "$disk" --query 'data.id' --raw-output)
      [ -n "$config" ] && args+=(--shape-config "$config")
      echo "$(date +%H:%M) round $round: $shape ${config:-}"
      if out=$(oci compute instance launch "${args[@]}" 2>&1); then
        instance="$out"
        echo "Created: $shape ${config:-}"
        break
      fi
      case "$out" in
        *"Out of host capacity"*|*"Out of capacity"*|*"TooManyRequests"*|*"InternalError"*) ;;
        *) echo "$out" | tail -5
           echo "Stopped: this is not a capacity problem; send this message to fix the script." >&2
           exit 1 ;;
      esac
    done
    [ -n "$instance" ] || sleep 120
  done
fi

echo "Waiting for the server to start..."
oci compute instance get --instance-id "$instance" --wait-for-state RUNNING >/dev/null 2>&1
ip=$(oci compute instance list-vnics --instance-id "$instance" --query 'data[0]."public-ip"' --raw-output)
cat <<DONE

The server is running. GitHub secrets (Settings -> Secrets and variables -> Actions):

  ORACLE_HOST     $ip
  ORACLE_SSH_KEY  the whole of the key printed by:  cat ~/.ssh/langsite

Also open ports 80 and 443 in langsite-vcn's Default Security List, and add
ORACLE_APP_ENV (the settings from Render). The first boot installs everything
in about 10 minutes.
DONE
