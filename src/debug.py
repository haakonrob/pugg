import sys
from pugg.main import pugg

if sys.platform == 'win32':
    pugg(('mathematics', 'laplace', '--dir=D:/onedrive/notes/'))
elif sys.platform == 'linux':
    pugg(('mathematics', 'laplace', '--dir=/home/haakonrr/OneDrive/notes/'))