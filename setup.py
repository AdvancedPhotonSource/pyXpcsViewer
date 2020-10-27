
from setuptools import setup, find_packages
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(name='xpcs_viewer',
      version='0.1',
      description='Python based XPCS viwer',
      scripts=['run_viewer'],
      url='https://github.com/AZjk/xpcs_gui',
      packages=find_packages(),
      author='Miaoqi Chu',
      install_requires=requirements,
      author_email='mqichu@anl.gov',
      license='Argonne National Laboratory License',
      zip_safe=False)
