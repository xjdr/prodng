ProdNG
======

Production Server images based on the [ProdNG whitepaper](docs/ProdNG-WhitePaper.pdf).

## But why?
Prodng was specifically created for the purpose of running large, distributed
production workloads in a very stable manner. The focus for prodng is not
integrating the next new hotness, it is to provide a stable platform with a
focus on operational stability and visibility.

## But Docker?
Docker is great for development and prodng can even parse dockerfiles.

However, generally speaking, docker does not focus no failure modes or
long term stability. Nor should it (IMHO), as a developer focused
tool, adding new features is more important in most cases. The docker
runtime also leaves a lot to be desired in terms of controlling your namespaces,
the entire networking layer and permissions. I am excited about the work being
done on libnetworking and libcontainer, but as these facilities already exist
in the linux kernel, I think we can do better from an operational perspective with
a focus on stability.

## But what is it?
ProdNG is a minimal debian jessie based distro focused on running services in hermetic chroots.

- Everything is a .deb ... Everything
- Services do not have access to the root filesystem
- All build operations and running services are to be hermetic (do not modify the rootfs or neighboring chroot's resources)

## What's it made of
+ (Very) Minimal Debian Jessie root
+ A forked version of [LMCTFY](https://github.com/xjdr/lmctfy)
+ [Osquery](https://github.com/facebook/osquery)
+ prodng-agent written with [Proxygen](https://github.com/facebook/proxygen)

## How do I use it?
By default there are 3 template chroots to build from:
    - prodng-build (Prodng image with build-essentials)
    - jessie (minimal jessie)
    - trusty (minimal trusty)

To build a new .deb or to run a service you would:

``` bash
$ prodng trusty my_service.deb dhcp
```

This would create a BTRFS copy-on-write hermetic chroot env with isolated namespaces and networking system

## But how about operations?

``` bash
$ prodng ls

< ls output >

$ prodng kill <name>

$ prodng freeze <name>

$ prodng thaw <name>
```

## Fine, fine ... But REST is the new hotness ...

``` bash
$ curl https://localhost:1337/prodng/ls

$ curl -X POST https://localhost:1337/prodng/kill?<name>

$ curl -X POST https://localhost:1337/prodng/freeze?<name>

$ curl -X POST https://localhost:1337/prodng/thaw?<name>

```

You get the idea ... the REST interface will have a correlating CLI action. 
