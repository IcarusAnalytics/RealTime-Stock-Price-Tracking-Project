from setuptools import find_packages,setup
from typing import List


HYPHEN_E_DOT='-e .'
def get_requirements(file_path:str)->List[str]:
    requiremnts=[]
    with open(file_path) as file_obj:

        requirements=file_obj.readlines()
        requirements=[req.replace("\n","")for req in requirements]

        if HYPHEN_E_DOT in requiremnts:
            requirements.remove(HYPHEN_E_DOT)


setup(name='RealTime Stock Price Tracker',version='0.1', author='Icarus Analytics', author_email='analyticsicarus@gamil.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt'))
