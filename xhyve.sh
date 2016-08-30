#!/bin/bash
# unfortunately debian currently panics in xhyve

tmp=$(mktemp -d)
pushd "$tmp"

iso="$HOME"/Downloads/debian-8.3.0-amd64-netinst.iso
echo "fixing disk"
dd if=/dev/zero bs=2k count=1 of=tmp.iso
dd if="$iso" bs=2k skip=1 >> tmp.iso

echo "mounting disk"
diskinfo=$(hdiutil attach tmp.iso)
disk=$(echo "$diskinfo" |  cut -d' ' -f1)
mnt=$(echo "$diskinfo" | perl -ne '/(\/Volumes.*)/ and print $1')
echo "mounted as $disk at $mnt"

echo "extracting kernel"
ls "$mnt"
cp "$mnt/install.amd/vmlinuz" .
cp "$mnt/install.amd/initrd.gz" .
diskutil eject "$disk"

echo "creating hdd"
dd if=/dev/zero of=hdd.img bs=100m count=1

KERNEL="vmlinuz"
INITRD="initrd.gz"
CMDLINE="earlyprintk=serial console=ttyS0 acpi=off"

MEM="-m 1G"
#SMP="-c 2"
NET="-s 2:0,virtio-net"
IMG_CD="-s 3,ahci-cd,$iso"
IMG_HDD="-s 4,virtio-blk,hdd.img"
PCI_DEV="-s 0:0,hostbridge -s 31,lpc"
LPC_DEV="-l com1,stdio"
ACPI="-A"

# shellcheck disable=SC2086
sudo xhyve $ACPI $MEM $SMP $PCI_DEV $LPC_DEV $NET $IMG_CD $IMG_HDD -f kexec,$KERNEL,$INITRD,"$CMDLINE"

popd
rm -rf "$tmp"
