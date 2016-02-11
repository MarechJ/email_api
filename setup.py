from setuptools import setup, find_packages
setup(
    name = 'email_api',
    version = '0.1',
    packages = find_packages(),

    install_requires = ['bottle>=0.12.9', 'email-validator>=1.0.0'],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst']
    },

    # metadata for upload to PyPI
    author = "Julien Marechal",
    author_email = "julien.marechal35@example.com",
    description = "API to send email through through parties API",
    license = "PSF",
    keywords = "API email smtp",
    url = "http://example.com/HelloWorld/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
