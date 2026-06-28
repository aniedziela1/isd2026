osboxes@hp-a:/usr/local/sbin$ cat t5-node-*
#!/bin/sh
set -eu
/usr/sbin/ip link set dev ens38 down
/usr/sbin/ip link set dev ens33 down
