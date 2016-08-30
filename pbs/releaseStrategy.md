# Release Strategy

Here are the best practices we want to follow for releasing the ProdNG image to public

Github Branch
-----------------
There are 2 github branches, "*master*" and "*development*" for the following purpose:

1. development - All the Pull request should be merged in the development branch. The CI job running against this branch will perform all the tests and verification.
Also the image will be published to Blackbird project only. Once the image is tested, this branch will be merged into master for the actual release.

2. master - The CI job running from master branch will create an artifact to be released to public. The image will be pushed to C3 with public access.

Versioning
----------

version number : x.x.x_RCx for Major.Minor.Patch_(Optional RC for testing)
For e.g.  0.6.3_RC1

The image created from __development__ branch should have RC in front of the version just to identify that it needs testing.
The image created from __master__ branch will just have x.x.x without RC. Once the image has been released from master, we can tag the commit with the version number.

Image name convention: `prodng_<manifest>_<version>.vmdk`
For e.g. `prodng_dev_0.1.1_RC1.vmdk`
