
from setuptools import setup, find_packages
with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(name='xpcs_viewer',
      version='0.242',
      description='A python-based interactive visualization tool to view XPCS dataset',
      scripts=['run_viewer.bat', 'run_viewer'],
      url='https://github.com/AdvancedPhotonSource/pyXpcsViewer',
      packages=find_packages(),
      include_package_data=True,
      author='Miaoqi Chu',
      install_requires=requirements,
      author_email='mqichu@anl.gov',
      license='Argonne National Laboratory License',
      zip_safe=False)
