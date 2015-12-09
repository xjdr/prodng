#!/bin/bash

set -ef -o pipefail

# This script assumes that debootstrap and parted are installed on the
# host system. As we are manipulating disks this script needs to be run
# as root.

INSTALL_ROOT=/mnt
INSTALL_DISK=/dev/sda

## Ensure you are running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

## Ensure disk is empty
dd if=/dev/zero of=$INSTALL_DISK bs=512 count=4

## Create partitions
parted -s -- $INSTALL_DISK mklabel GPT
parted -s -- $INSTALL_DISK unit MB mkpart primary ext2 1 256
parted -s -- $INSTALL_DISK set 1 boot on 
parted -s -- $INSTALL_DISK unit MB mkpart primary ext4 257 1257
parted -s -- $INSTALL_DISK unit MB mkpart primary ext4 1258 20000
parted -s -- $INSTALL_DISK unit MB mkpart primary xfs  20001 -0

## Create filesystems
mkfs.ext2 ${INSTALL_DISK}2 > /dev/null
mkfs.ext4 ${INSTALL_DISK}1 > /dev/null
mkfs.xfs -f ${INSTALL_DISK}3 > /dev/null
mkfs.xfs -f ${INSTALL_DISK}4 > /dev/null

## Mount the target drive
mount ${INSTALL_DISK}2 ${INSTALL_ROOT}
mkdir ${INSTALL_ROOT}/boot
mount ${INSTALL_DISK}1 ${INSTALL_ROOT}/boot
mkdir ${INSTALL_ROOT}/var
mount ${INSTALL_DISK}3 ${INSTALL_ROOT}/var

## Install minimal debian 
debootstrap \
--arch=amd64 \
--variant=minbase \
--include=netbase,ifupdown,net-tools,isc-dhcp-client,linux-base,sysvinit-core,sysvinit-utils,vim-tiny,linux-image-amd64 \
jessie \
$INSTALL_ROOT

##create /etc/fstab
cat > ${INSTALL_ROOT}/etc/fstab <<EOF

# /etc/fstab: static file system information.
#
# file system    mount point   type    options                  dump pass
${INSTALL_DISK}2        /             ext4    defaults                 0    1
${INSTALL_DISK}1        /boot         ext2    ro,nosuid,nodev          0    2

proc                    /proc         proc    defaults                 0    0

${INSTALL_DISK}3        /var          xfs    rw,nosuid,nodev           0    2
${INSTALL_DISK}4        /srv          xfs    rw,nodev                  0    2

EOF

## Configure networking
cat > ${INSTALL_ROOT}/etc/network/interfaces <<EOF
######################################################################
# /etc/network/interfaces -- configuration file for ifup(8), ifdown(8)
# See the interfaces(5) manpage for information on what options are
# available.
######################################################################

auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp

EOF

echo ProdNG-Base > ${INSTALL_ROOT}/etc/hostname

cat > ${INSTALL_ROOT}/etc/hosts <<EOF
127.0.0.1 localhost ProdNG-Base

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
EOF

## Cleanup
rm $INSTALL_ROOT/var/cache/apt/archives/*
rm $INSTALL_ROOT/var/cache/apt/*.bin
rm $INSTALL_ROOT/var/lib/apt/lists/*
rm $INSTALL_ROOT/var/log/dpkg.log*
rm $INSTALL_ROOT/var/log/apt/*

## Open a shell for troubleshooting
mount -o bind /dev $INSTALL_ROOT/dev
mount -o bind /proc ${INSTALL_ROOT}/proc
mount -o bind /sys ${INSTALL_ROOT}/sys
mkdir ${INSTALL_ROOT}/var/dev
#mount -t tmpfs tmpfs ${INSTALL_ROOT}/var/dev/shm
#mount -t devpts devpts ${INSTALL_ROOT}/dev/pts

echo "Please insall a bootloader and set a root passwd"

LANG=C chroot $INSTALL_ROOT DEBIAN_FRONTEND=noninteractive apt-get purge systemd
LANG=C chroot $INSTALL_ROOT DEBIAN_FRONTEND=noninteractive apt-get install -y sysvinit sysvinit-utils

LANG=c chroot $INSTALL_ROOT /bin/bash
export TERM=xterm-color
