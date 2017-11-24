from setuptools import setup, find_packages

setup(
    name='email_api',
    version='0.1',
    packages=find_packages(exclude=['tests']),

    install_requires=[
        'bottle>=0.12.9',
        'email-validator>=1.0.0',
        'requests>=2.9.1',
        'PyYAML>=3.11'
    ],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst']
    },

    # metadata for upload to PyPI
    author="Julien Marechal",
    author_email="julien.marechal35@example.com",
    description="API to send email through through parties API",
    license="BSD",
    keywords="API email smtp",
    url="https://github.com/MarechJ/email_api",
    # could also include long_description, download_url, classifiers, etc.
)
