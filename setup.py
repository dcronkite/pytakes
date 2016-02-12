from setuptools import setup

setup(name='pytakes',
      version='0.1',
      description='Basic information extraction tool.',
      url='https://bitbucket.org/dcronkite/pytakes',
      author='dcronkite',
      author_email='dcronkite-gmail-com',
      license='MIT',
      classifiers=[  # from https://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python :: 3 :: Only',
      ],
      keywords='nlp information extraction',
      packages=['pytakes'],
      entry_points=['automate_run.py',
                    'negex_creator.py',
                    'processor.py',
                    'postprocessor.py',
                    'sendmail.py'],
      install_requires=[],
      zip_safe=False
      )
