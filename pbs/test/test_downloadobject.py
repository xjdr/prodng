import unittest
import os,time
import shutil

from pbs.bin.main import download_package,build_uri

class TestDownloadObject(unittest.TestCase):
  repoyml = "prodng/repo.yml"
  dep = [{"name":"glibc/multiarch-support_2.19-18+deb8u3_amd64.deb","repo":"security","url":"http://security.debian.org/debian-security/pool/updates/main/g/glibc/multiarch-support_2.19-18+deb8u3_amd64.deb"},
         {"name": "mawk/mawk_1.3.3-17_amd64.deb","repo": "main", "url":"http://ftp.us.debian.org/debian/pool/main/m/mawk/mawk_1.3.3-17_amd64.deb"},
         {"name": "libs/libselinux/libselinux1_2.3-2_amd64.deb","repo": "main", "url":"http://ftp.us.debian.org/debian/pool/main/libs/libselinux/libselinux1_2.3-2_amd64.deb"}]

  def test_build_uri(self):
    for d in self.dep:
      do = build_uri(d,self.repoyml)
      self.assertEqual(do,d["url"])

  def test_download_dep(self):
      pkg_path = "packages"
      for d in self.dep:
          pkg_name = d['name'].split('/')[-1]
          do = download_package(pkg_name,pkg_path,d['url'])
          file = os.path.join(pkg_path,pkg_name)
          self.assertTrue(os.path.exists(file))
          self.assertGreaterEqual(os.stat(file).st_size,0)
      shutil.rmtree(pkg_path)

if __name__ == '__main__':
    unittest.main()
