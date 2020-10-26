#from distutils.core import setup
from setuptools import setup
import dasmon_listener

SETUP_ARGS = dict(
    name="dasmon_listener",
    version=dasmon_listener.__version__,
    description="SNS DASMON listener",
    author='NScD Oak Ridge National Laboratory',
    author_email='ndav@email.ornl.gov',
    url="http://neutrons.github.com/",
    license='GNU LGPL',
    long_description=open('dasmon_listener/README.md').read(),
    platforms=['POSIX'],
    options={'clean': {'all': 1}},
    zip_safe = False,
    entry_points = {
                    'console_scripts':[
                                       "dasmon_listener = dasmon_listener.listener_daemon:run",
                                       "reduction_update = dasmon_listener.reduction_script_update:run",
                                       ]
                    },
    packages=["dasmon_listener"],
        classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Networking',
        ],

)

if __name__ == '__main__':
    setup(**SETUP_ARGS)
