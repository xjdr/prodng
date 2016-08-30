import unittest
import os,time
import shutil

from pbs.bin.main import run

class TestRunCommand(unittest.TestCase):

   def test_run(self):
     print run("echo hello")
     self.assertEqual(run("echo hello"),0)

     print run("wrong_cmd")
     self.assertTrue((run("wrong_cmd"))!=0)

if __name__ == '__main__':
  unittest.main()