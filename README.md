ProdNG
======

==== ProdNG has been running in production for a while and things have changed a bit from the original vision.
Please find the update version with more than a year of operational verification in very demanding environments. ===

We are going to be slowly releasing our current production tooling as we are able to remove any PayPal specific code / settings. 
Once that process is complete, I will remove this section and update the docs.

Production Server images based on the [ProdNG whitepaper](docs/ProdNG-WhitePaper.pdf).

## But why?
Prodng was specifically created for the purpose of running large, distributed
production workloads in a very stable manner. The focus for prodng is not
integrating the next new hotness, it is to provide a stable platform with a
focus on security, operational stability and visibility. This means forensic audits,
sane defaults, and exceptional monitoring capabilities.

## But Docker?
Docker is great for development and testing.

However, generally speaking, docker does not focus on failure modes or
long term stability. Nor should it (IMHO), as a developer focused
tool, adding new features is more important in most cases. Docker the company
should be able to focus on generating revenue and those goals often conflict
with stable production runtimes. Security and stability can sometimes cause
friction with pure developer productivity, and therein lies the conflict.

The docker runtime also leaves a lot to be desired in terms of granularly controlling your namespaces,
networking layer and permissions. I am excited about the work being
done on libnetworking and libcontainer, but as these facilities already exist
in the linux kernel, I think we can do better from an operational perspective with
a focus on stability. I also think innovations in capabilities audit (expectation vs reality) and
per process monitoring are in their infancy in most of these platforms. 

Stability is boring, in the best possible ways.

## But what is it?
ProdNG is a minimal debian based distro focused on running services in hermetic chroots.

- Everything is a .deb ... Everything
- Services do not have access to the root filesystem
- All build operations and running services are to be hermetic (do not modify the rootfs or neighboring chroot's resources)

## What's it made of
+ Very small base image (no package manager, etc, just enough to bootstrap a jail) 
+ prodng-cli to allow you to manage and monitor jails
+ [Osquery](https://github.com/facebook/osquery)
+ prodng-agent to audit and enforce policy as well as provide visibility
+ Sysdig, google/grr, yara, etc for a sane production runtime

## What is a jail
A jail is a tightly controlled chroot with:
  - its own network (managed via mac-vlan)
  - bare minimum capabilities (in terms of the kernel)
  - root is mapped to normal user on the base
  - resource monitoring and isolation

## How do I use it?
You will need to crate a .deb with the jail template (see GettingStarted.md).
Once you have your app packaged, use the agent to install and start your app
in its own jail.

You can then use the prodng-cli to manage and monitor the process running in the jail.


