from setuptools import setup
import workflow

SETUP_ARGS = dict(
    name="workflow",
    version=workflow.__version__,
    description="SNS data workflow manager",
    author='NScD Oak Ridge National Laboratory',
    author_email='ndav@email.ornl.gov',
    url="http://neutrons.github.com/",
    license='GNU LGPL',
    long_description=open('README.md').read(),
    platforms=['POSIX'],
    options={'clean': {'all': 1}},
    zip_safe=False,
    entry_points={'console_scripts': ["workflowmgr = workflow.sns_post_processing:run", ]},
    packages=["workflow", "workflow.database", "workflow.database.report"],
        classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
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
