#!/bin/bash

set -e

INSTALL_ROOT=/mnt

## Create partitions
parted -s -- /dev/sda mklabel GPT
parted -s -- /dev/sda unit MB mkpart primary ext2 1 256
parted -s -- /dev/sda unit MB mkpart primary ext4 257 1257
parted -s -- /dev/sda unit MB mkpart primary ext4 1258 20000
parted -s -- /dev/sda unit MB mkpart primary xfs  20001 -0

## Create filesystems
mkfs.ext2 /dev/sda1 > /dev/null
mkfs.ext4 /dev/sda > /dev/null2
mkfs.xfs -f /dev/sda3 > /dev/null
mkfs.xfs -f /dev/sda4 > /dev/null

## Mount the target drive
mount /dev/sda2 $INSTALL_ROOT
mkdir $INSTALL_ROOT/boot
mount /dev/sda1 $INSTALL_ROOT/boot
mkdir $INSTALL_ROOT/var
mount /dev/sda3 $INSTALL_ROOT/var

## Install minimal debian 
debootstrap \
--arch=amd64 \
--variant=minbase \
--exclude=systemd \
--include=netbase,ifupdown,net-tools,isc-dhcp-client,linux-base,sysvinit-core,sysvinit-utils,vim-tiny,linux-image-amd64 \
jessie \
$INSTALL_ROOT

##create /etc/fstab
cat > $INSTALL_ROOT/etc/fstab <<EOF

# /etc/fstab: static file system information.
#
# file system    mount point   type    options                  dump pass
/dev/sda2        /             ext4    defaults                 0    1
/dev/sda1        /boot         ext2    ro,nosuid,nodev          0    2

proc             /proc         proc    defaults                 0    0

/dev/fd0         /media/floppy auto    noauto,rw,sync,user,exec 0    0
/dev/cdrom       /media/cdrom  iso9660 noauto,ro,user,exec      0    0

/dev/sda3        /var          xfs    rw,nosuid,nodev           0    2
/dev/sda4        /srv          xfs    rw,nodev                  0    2

EOF

#apt-get -y install locales
#sed 's/# en_US.UTF-8/en_US.UTF-8/' -i /etc/locale.gen
#locale-gen

## Configure networking

cat $INSTALL_ROOT/etc/network/interfacess <<EOF
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

echo ProdNG-Base > $INSTALL_ROOT/etc/hostname

cat $INSTALL_ROOT/etc/hosts <<EOF
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
mount -o bind /proc $INSTALL_ROOT/proc
mount -o bind /sys $INSTALL_ROOT/sys
mount -t tmpfs tmpfs $INSTALL_ROOT/var/dev/shm
mount -t devpts devpts $INSTALL_ROOT/dev/pts

LANG=c chroot $INSTALL_ROOT /bin/bash
export TERM=xterm-color
