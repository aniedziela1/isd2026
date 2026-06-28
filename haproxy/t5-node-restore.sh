#!/bin/sh
set -eu
/usr/sbin/ip link set dev ens33 up
/usr/sbin/ip link set dev ens38 up
sleep 1
/usr/sbin/ip -6 addr replace \
  2001:db8:20:10::2/64 dev ens33
/usr/sbin/ip -6 addr replace \
  2001:db8:20:0::2/64 dev ens38
/usr/bin/systemctl restart keepalived
osboxes@hp-a:/usr/local/sbin$ 