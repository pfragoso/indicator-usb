#!/usr/bin/env python
import commands

def run(c):
    return commands.getstatusoutput(c)[0]

def build(dir, name, ver, desc, deps):
    run('mkdir ' + dir + 'DEBIAN')
    
    l = (name, ver, ', '.join(deps), desc)
    i = 'Package: %s\nPriority: optional\nSection: gnome\nMaintainer: Eugeny Pankov <john.pankov@gmail.com>\nArchitecture: all\nVersion: %s\nDepends: %s\nDescription: %s\n' % l
    with open(dir + 'DEBIAN/control', 'w') as f:
        f.write(i)
        
    run('dpkg-deb -b ' + dir + ' ' + name + '-' + ver + '.deb')
    
run('mkdir -p deb/usr/bin')
run('mkdir -p deb/usr/share/icons/hicolor/22x22/status')

run('cp main.py deb/usr/bin/indicator-usb')
run('cp icon.png deb/usr/share/icons/hicolor/22x22/status/indicator-usb-panel.png')

build('deb/', 'indicator-usb', '0.2', 'Application indicator for easy USB device safe-removal', ['python-appindicator', 'python-gnome2', 'python-notify'])
run('rm -r deb')

