# tryton_maintain

A Python3 script to keep the Tryton Versions up to date on openSUSE Build Service. <br>
Tryton is an OpenSource ERP Framework ( http://www.tryton.org ) <br>
Packages for Tryton are maintained for openSUSE using the Open Build Service ( https://build.opensuse.org/ ) <br>
To make use of the script you need to have osc (comes with openSUSE) installed and have a working copy of the tryton-repository (e.g. osc co Application:ERP:Tryton:3.8 )

What the script does:
- read download.tryton.org/version and extract packages from the html code
- determine latest build version (e.g. tryton-3.8.10.tar.gz -> major version 3.8, build version 10)
- checks build version against version in local repository
- updates the build version in spec-file, if version on download.tryton.org is higher
- updates the version in changes file
- triggers local service run and checks changes into OBS

run tryton_maintain.py -h for options and parameters

As this is my first program in python3 - improvements are welcome

Axel Braun <axel.braun@gmx.de> 31.12.2016
