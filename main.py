#!/usr/bin/env python
import gobject
import gtk
import appindicator
import gnomevfs
import pynotify
import os

class Monitor:
    mon = None
    drives = {}
    ejecting = ''
    main = None
    show_hdd = True
    show_net = True
    
    def __init__(self, main):
        self.main = main

    def init(self):
        self.mon = gnomevfs.VolumeMonitor()
        self.mon.connect('volume-mounted', self.add_drive)
        self.mon.connect('volume-unmounted', self.del_drive)
        self.refresh()
                    
    def refresh(self):
        self.drives = {}
        for d in self.mon.get_mounted_volumes():
            self.add_drive(None, d)
    
    def add_drive(self, s, d):
        if d.is_user_visible() and d.is_mounted():
            if (d.get_device_path().startswith('/dev/') and self.show_hdd) \
               or (d.get_device_path().startswith('//') and self.show_net) :
                self.drives[d.get_device_path()] = d    
        self.main.update()
        
    def del_drive(self, s, d):
        for k in self.drives:
            if k == d.get_device_path():
                self.drives.pop(k)
                self.main.update()
                return
            
    def eject(self, s, d):
        self.ejecting = d
        d.eject(self.eject_cb)
        self.del_drive(None, d)
        
    def eject_cb(self, x, d):
        d = self.ejecting
        n = pynotify.Notification('Device can be removed now', d.get_display_name(), d.get_icon())
        n.show()
        
class Main:
    mon = None
    ind = None
    menu = None
    
    def __init__(self):
        self.ind = appindicator.Indicator('indicator-usb', 'indicator-usb-panel', appindicator.CATEGORY_HARDWARE)
        self.ind.set_status(appindicator.STATUS_PASSIVE)

        self.mon = Monitor(self)

        try:
            ss = open(os.path.expanduser('~/.config/indicator-usb')).read().split('\n')
            self.mon.show_hdd = ss[0] == '1'
            self.mon.show_net = ss[1] == '1'
        except:
            pass
        
        self.mon.init()
        self.save_config()
           
    def save_config(self):
        s = ''
        with open(os.path.expanduser('~/.config/indicator-usb'), 'w') as f:
            f.write('%i\n%i\n' % ((1 if self.mon.show_hdd else 0), (1 if self.mon.show_net else 0)))
        self.mon.refresh()    
             
    def update(self):
        self.ind.set_status(
            appindicator.STATUS_ACTIVE if len(self.mon.drives) > 0 else
            appindicator.STATUS_PASSIVE)
            
        if self.menu is not None:
            self.menu.destroy()
            
        self.menu = gtk.Menu()

        # Header
        hdr = gtk.MenuItem('Safely remove devices')
        hdr.set_sensitive(False)
        hdr.show()
        self.menu.append(hdr)
        
        # Separator
        smi = gtk.SeparatorMenuItem()
        smi.show()
        self.menu.append(smi)
        
        for k in self.mon.drives:
            i = self.mon.drives[k]
            mi = gtk.ImageMenuItem(i.get_display_name())
            try:
                mi.set_image(gtk.image_new_from_stock(i.get_drive().get_icon(), gtk.ICON_SIZE_MENU))
            except:
                mi.set_image(gtk.image_new_from_stock(i.get_icon(), gtk.ICON_SIZE_MENU))
                
            self.menu.append(mi)
            mi.show()
            mi.connect('activate', self.mon.eject, i)

        # Separator
        smi = gtk.SeparatorMenuItem()
        smi.show()
        self.menu.append(smi)

        # Options
        mi = gtk.MenuItem('Devices')
        mi.show()
        self.menu.append(mi)

        om = gtk.Menu()
        om.show()
        mi.set_submenu(om)
        
        m = gtk.CheckMenuItem('Disks')
        m.set_active(self.mon.show_hdd)
        m.connect('activate', self.on_option, 'hdd')
        m.show()
        om.append(m)

        m = gtk.CheckMenuItem('Network folders')
        m.set_active(self.mon.show_net)
        m.connect('activate', self.on_option, 'net')
        m.show()
        om.append(m)
        
        self.ind.set_menu(self.menu)

    def on_option(self, x, o):
        if o == 'hdd':
            self.mon.show_hdd = x.get_active()
        if o == 'net':
            self.mon.show_net = x.get_active()
        self.save_config()
        
            
m = Main()
gtk.main()
        
