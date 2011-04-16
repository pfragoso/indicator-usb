#!/usr/bin/python
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import AppIndicator
from gi.repository import Notify

import os

#YUCK: Gtk.image_new_from_gicon does not work, and pynotify does
#not support gicon, so just let the theme choose the icon
def _get_icon_name_from_gicon(gicon):
    assert type(gicon) == Gio.ThemedIcon
    name = "image-missing"
    theme = Gtk.IconTheme.get_default()
    for n in gicon.get_names():
        if theme.lookup_icon(n, Gtk.icon_size_lookup(Gtk.IconSize.MENU, 0, 0), 0):
            name = n
            break
    return n

    
class Monitor:

    mon = None
    drives = []
    main = None
    show_hdd = True
    show_net = True

    def __init__(self, main):
        self.main = main

    def init(self):
        self.mon = Gio.VolumeMonitor.get()
        self.mon.connect('mount-added', self._add_drive)
        self.mon.connect('mount-removed', self._del_drive)
        self.refresh()

    def _add_drive(self, s, m):
        if m.can_unmount():
            root = m.get_root()
            if (root.get_uri_scheme() == "file" and self.show_hdd) \
               or (not root.is_native() and self.show_net) :
                self.drives.append(m)
        self.main.update()

    def _del_drive(self, s, d):
        self.drives.remove(d)
        self.main.update()

    def refresh(self):
        self.drives = []
        for m in self.mon.get_mounts():
            self._add_drive(None, m)

    def _eject_cb(self, m, result, t):
        #XXX: pynotify does not support gicon
        Notify.init('indicator-usb')
    	n = Notify.Notification.new('Device can be removed now', m.get_name(), _get_icon_name_from_gicon(m.get_icon()))
    	n.show()

    def eject(self, s, m):
        m.unmount(Gio.MountUnmountFlags.NONE, None, self._eject_cb, None)



class Main:
    mon = None
    ind = None
    menu = None

    def __init__(self):
        #if running from source directory set a known icon
        if os.path.exists("icon.png"):
            icon = 'image-missing'
        else:
            icon = 'indicator-usb-panel'
        self.ind = AppIndicator.Indicator.new('indicator-usb', icon, AppIndicator.IndicatorCategory.HARDWARE)
        self.ind.set_status(AppIndicator.IndicatorStatus.PASSIVE)

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
            AppIndicator.IndicatorStatus.ACTIVE if len(self.mon.drives) > 0 else
            AppIndicator.IndicatorStatus.PASSIVE)
        if self.menu is not None:
            self.menu.destroy()

        self.menu = Gtk.Menu()

        # Header
        hdr = Gtk.MenuItem(label='Safely remove devices')
        hdr.set_sensitive(False)
        hdr.show()
        self.menu.append(hdr)

        # Separator
        smi = Gtk.SeparatorMenuItem()
        smi.show()
        self.menu.append(smi)

        for i in self.mon.drives:
            mi = Gtk.ImageMenuItem(label=i.get_name())
            #XXX: gicon does not work...
            mi.set_image(Gtk.Image.new_from_stock(_get_icon_name_from_gicon(i.get_icon()), Gtk.IconSize.MENU))
            self.menu.append(mi)
            mi.show()
            mi.connect('activate', self.mon.eject, i)

        # Separator
        smi = Gtk.SeparatorMenuItem()
        smi.show()
        self.menu.append(smi)

        # Options
        mi = Gtk.MenuItem(label='Devices')
        mi.show()
        self.menu.append(mi)

        om = Gtk.Menu()
        om.show()
        mi.set_submenu(om)

        m = Gtk.CheckMenuItem(label='Disks')
        m.set_active(self.mon.show_hdd)
        m.connect('activate', self.on_option, 'hdd')
        m.show()
        om.append(m)

        m = Gtk.CheckMenuItem(label='Network folders')
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
Gtk.main()

