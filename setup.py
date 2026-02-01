# from setuptools import setup
# from setuptools.command.develop import develop
# from setuptools.command.install import install
# import subprocess
# import sys

# class PostInstallCommand(install):
#     def run(self):
#         install.run(self)
#         print("Initializing database...")
#         subprocess.check_call([sys.executable, "-m", "app.utils.db_init"])

# setup(
#     cmdclass={
#         'install': PostInstallCommand,
#     }
# )