from distutils.core import setup
import setuptools

setup(name='pytakes',
      version='0.3',
      description='Basic information extraction tool.',
      url='https://bitbucket.org/dcronkite/pytakes',
      author='dcronkite',
      author_email='dcronkite-gmail',
      license='MIT',
      classifiers=[  # from https://pypi.python.org/pypi?%3Aaction=list_classifiers
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Text Processing :: Linguistic',
      ],
      keywords='nlp information extraction',
      entry_points={
          'console_scripts':
              [
                  'pytakes-automate-run = pytakes.automate_run:main',
                  'pytakes-negex-creator = pytakes.negex_creator:main',
                  'pytakes-postprocessor = pytakes.postprocessor:main',
                  'pytakes-processor = pytakes.processor:main',
                  'pytakes-sendmail = pytakes.sendmail:main',
                  'pytakes-build-dictionary = pytakes.build_dictionary:main',
              ]
      },
      install_requires=['regex', 'pyodbc', 'jinja2'],
      package_dir={'': 'src'},
      packages=setuptools.find_packages('src'),
      package_data={'pytakes.nlp': ['data/*.db']},
      zip_safe=False
      )
