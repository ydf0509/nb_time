# coding=utf-8
from pathlib import Path
from setuptools import setup, find_packages
import os

# with open("README.md", "r",encoding='utf8') as fh:
#     long_description = fh.read()

# filepath = ((Path(__file__).parent / Path('README.md')).absolute()).as_posix()
filepath = 'README.md'
print(filepath)


extra_requires = {}
install_requires = [
    'tzlocal',
    'pytz',
    'pydantic',

]

# if os.name == 'nt':
#     install_requires.append('pywin32')

print(f'nb_time install_requires:{install_requires}')
setup(
    name='nb_time',  #
    version="0.7",
    description=(
        'Awesome time conversion handling with support for chaining operations. '
    ),
    keywords=['arrow','time','datetime','time_utils'],
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    long_description_content_type="text/markdown",
    long_description=open(filepath, 'r', encoding='utf8').read(),
    url='https://github.com/ydf0509/nb_time',
    # data_files=[filepath],
    author='bfzs',
    author_email='ydf0509@sohu.com',
    maintainer='ydf',
    maintainer_email='ydf0509@sohu.com',
    license='BSD License',
    packages=find_packages(),
    include_package_data=True,
    platforms=["all"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=install_requires,
    extras_require = extra_requires
)
"""
打包上传
python setup.py sdist upload -r pypi




python setup.py sdist ; python -m  twine upload dist/nb_time-0.1.tar.gz

twine upload dist/*


python -m pip install nb_time --upgrade -i https://pypi.org/simple   # 及时的方式，不用等待 阿里云 豆瓣 同步
"""
