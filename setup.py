from distutils.core import setup

setup(
    name='openabis-fingerjetfx',
    version='0.0.1',
    packages=['openabis_fingerjetfx'],
    url='https://github.com/newlogic42/openabis-fingerjetfx',
    license='Apache License',
    author='newlogic42',
    author_email='',
    description='OpenAbis\' plugin implementation of FingerJetFXOSE/FingerJetFXOSE.',
    install_requires=[
        'pillow==6.2.1'
    ],
    package_data={
        '': ['*'],
    }
)
