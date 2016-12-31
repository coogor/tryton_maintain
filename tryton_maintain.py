#!/usr/bin/python3

# Maintenance program for Tryton on OBS 

##############################################################################
#
#    tryton_maintain
#    Copyright (C) 2016 Axel Braun <axel.braun@gmx.de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#
# Flags
# -d local working directory - without the version in the back
# -v Tryton version to update
# -f Run update on factory
# -u update local working directory
# -s run local service
# -r Issue submit request
#
VERSION="0.1"

# Einige Defaults - werden von argparse übersteuert
tryton_url = "http://downloads.tryton.org"
local_dir = "/home/docb/buildservice/Application:ERP:Tryton:" 
version_dir = "3.8"
result = []

import argparse
import sys
import urllib.request
import re
import natsort as ns
import os
import subprocess

def specsearch(s_module, h_version, l_dir):
    """Searchs for Version in the Specfile"""
    ergebnis = False
    try:
        os.chdir(l_dir + "/" + s_module)
    except FileNotFoundError as e:
        print( "Error: %s" % str(e) )
        ergebnis = False
        return ergebnis
    try: 
        fobj = open(s_module + ".spec")
    except FileNotFoundError as e:
        print( "Error: %s" % str(e) )
        ergebnis = False
        return ergebnis

    for line in fobj:
        x = re.search(r"^Version:.",line.rstrip())
        if x != None:
# Versionsnummer bestimmen:
            z = re.search(r"[0-9]{,2}$", line.rstrip()).group(0)
            if h_version > z:
#            version ersetzen und weitere Aktionen
                print("*** Größere Version für " , s_module , " gefunden: ", h_version , " aktuell: " , z)
                ergebnis = True
                fobj.close()
                return ergebnis
                break
            else:
                ergebnis = False

    fobj.close()       
    return ergebnis 

def replace_spec(s_module, h_version, l_dir):
    ergebnis = False
    try:
        os.chdir(l_dir + "/" + s_module)
    except FileNotFoundError as e:
        print( "Error: %s" % str(e) )
        ergebnis = False
        return ergebnis
    try: 
        fobj_in = open(s_module + ".spec")
    except FileNotFoundError as e:
        print( "Error: %s" % str(e) )
        ergebnis = False
        return ergebnis

    fobj_out = []
    for line in fobj_in:
        x = re.search(r"^Version:.",line.rstrip())
        if x == None: 
#            alten Wert raus schreiben
            fobj_out.append(line)
        else:
# Versionsnummer bestimmen:
            print("Version für " , s_module , " gesetzt: ", h_version )
            fobj_out.append("Version:        %{majorver}." + h_version + "\n")
            ergebnis = True

    try: 
        fobj = open(s_module + ".spec", "w")
    except FileNotFoundError as e:
        print( "Error: %s" % str(e) )
        ergebnis = False
        return ergebnis
    
    for line in fobj_out:
        fobj.write(line)
        
    fobj.close()          
    return ergebnis

def do_osc(cmd, message = "" , rest = ""):
    if message != "":
        cmd += " -m '" + message + "' " + rest 
    p=subprocess.Popen( cmd , shell=True )
    if p.wait() == 0:
        print(cmd , " gelaufen")

parser = argparse.ArgumentParser()

parser.add_argument("version", help="Tryton Version to update (like 3.8, 4.2 etc)")
parser.add_argument("dir", help="local OBS working directory (like /home/user/Application:ERP:Tryton:)")
parser.add_argument("-f", help="Update FACTORY - requires correct version!",  action="store_true")
parser.add_argument("-u", help="Update local working copy (osc up)",  action="store_true")
parser.add_argument("-s", help="run local service (osc service localrun)",  action="store_true")
parser.add_argument("-r", help="issue submit request to (1)target with (2)comment (like osc sr -m comment (from and package automatically filled) target",  nargs=2)

args = parser.parse_args()

version_dir = args.version
local_dir = args.dir
        
tryton_url += "/" + version_dir
# lokales arbeitsdirectory
if args.f:
    local_dir += "Factory"
else:
    local_dir += version_dir

print("URL:         " , tryton_url)
print("Lokaler Pfad:" , local_dir)

try:
    os.chdir(local_dir)
except FileNotFoundError as e:
    print( "Error: %s" % str(e) )
    sys.exit()
    
if args.u:
    print("Update of local work copy requested")
    do_osc("osc up")

###################################
# Webseite lesen
###################################

local_filename, headers = urllib.request.urlretrieve(tryton_url)

print("Lokaler Dateiname: " , local_filename)

###################################
# Parsen der Webseite nach *tar.gz , tgz
###################################

fobj = open(local_filename)

for line in fobj:
    x = re.search(r"tryton[-_.a-zA-Z0-9]*z",line.rstrip())
    if x != None:
      result.append(x.group(0))
# proteus
    else:
        x = re.search(r"proteus-[.a-zA-Z0-9]*z",line.rstrip())
        if x != None:
            result.append(x.group(0))
fobj.close()

# Eindeutige Liste:
t = list(set(result))

# Sortieren
t = ns.natsorted(t,reverse=True)

###################################
# Endung tar.gz entfernen
###################################
print("Die Endung entfernen und in Tupel aufteilen")

result = []

for line in t:
    x = re.sub(r".t[ar.]*gz$", "", line)
    if x != None:
      y = x.split("-")
      y[1] = re.search(r"[0-9]{,2}$", y[1]).group(0)
      if y[1] != None and y[1] != "":
        result.append(y)

###################################
# Den ersten Eintrag jeweils prüfen, of das spec file 
# der version entspricht
###################################

saved_module = ()
ergebnis = ""
counter = 0

for liste in result:
    
    if liste[0] != saved_module:
        # Neues Modul, checken
        saved_module = liste[0]
        high_version = liste[1]
        
        if specsearch(saved_module, high_version, local_dir) == True:
            counter += 1
            print("Modul mit höherer Version: ", saved_module)
            replace_spec(saved_module, high_version, local_dir)

# Setzen version control
            text = "Version " + version_dir + "." + high_version
            do_osc("osc vc", text)

# trigger_servicerun
            if args.s:
                do_osc("osc service localrun")

# geänderte Dateien bekannt machen
            do_osc("osc ar")

# in OBS einchecken
            text = "Update to " + saved_module + " " + text
            do_osc("osc ci" , text)

# submit request
            if args.r:
                text = args.r[1]
                if args.f:
                    rest = "Application:ERP:Tryton:Factory"
                else:
                    rest = "Application:ERP:Tryton:" + version_dir + " " + saved_module + " " + args.r[0]
                do_osc("osc sr", text, rest)
    
print( counter , " Module aktualisiert")

