# This file is part of MyPaint.
# Copyright (C) 2010 by Martin Renold <martinxyz@gmx.ch>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from gettext import gettext as _
import gtk, gobject, pango
gdk = gtk.gdk
import windowing


class Window(windowing.SubWindow):
    def __init__(self, app):
        windowing.SubWindow.__init__(self, app)
        self.last_selected_brush = None

        self.set_title(_('Input Device Test'))
        self.set_role('Test')
        self.connect('delete-event', self.app.hide_window_cb)
        self.connect('map-event', self.map_cb)
        gobject.timeout_add(1000, self.second_timer_cb, priority=gobject.PRIORITY_HIGH)

        self.initialized = False
        self.unreported_motion = None
        self.suppressed = 0
        self.motion_counter = 0
        self.last_device = None

        #main container
        vbox = gtk.VBox()
        self.add(vbox)

        table = gtk.Table(2, 4)
        vbox.pack_start(table, expand=False, fill=True)

        def add(row, name, value_widget):
            l1 = gtk.Label(name)
            l1.set_justify(gtk.JUSTIFY_LEFT)
            l1.set_alignment(0.0, 0.5)
            l2 = value_widget
            l2.set_alignment(0.0, 0.5)
            table.attach(l1, 0, 1, row, row+1, gtk.FILL, 0, 5, 0)
            table.attach(l2, 1, 2, row, row+1, gtk.FILL, 0, 5, 0)

        l = self.pressure_label = gtk.Label(_('(no pressure)'))
        add(0, _('Pressure:'), l)

        l = self.tilt_label = gtk.Label(_('(no tilt)'))
        add(1, _('Tilt:'), l)

        l = self.motion_counter_label = gtk.Label()
        add(2, 'MOTION_NOTIFY:', l)

        l = self.device_label = gtk.Label(_('(no device)'))
        add(3, _('Device:'), l)

        vbox.pack_start(gtk.HSeparator(), expand=False, fill=False)

        tv = self.tv = gtk.TextView()
        tv.set_editable(False)
        tv.modify_font(pango.FontDescription("Monospace"))
        tv.set_cursor_visible(False)
        vbox.pack_start(tv, expand=True, fill=True)
        self.log = []

    def second_timer_cb(self):
        self.motion_counter_label.set_text(str(self.motion_counter))
        self.motion_counter = 0
        return True

    def event2str(self, event):
        t = str(getattr(event, 'time', '-'))
        msg = '% 6s % 15s' % (t[-6:], event.type.value_name.replace('GDK_', ''))

        if hasattr(event, 'x') and hasattr(event, 'y'):
            msg += ' x=% 7.2f y=% 7.2f' % (event.x, event.y)

        pressure = event.get_axis(gdk.AXIS_PRESSURE)
        if pressure is not None:
            self.pressure_label.set_text('%4.4f' % pressure)
            msg += ' pressure=% 4.4f' % pressure

        if hasattr(event, 'state'):
            msg += ' state=0x%04x' % event.state

        if hasattr(event, 'button'):
            msg += ' button=%d' % event.button

        if hasattr(event, 'keyval'):
            msg += ' keyval=%s' % event.keyval

        if hasattr(event, 'hardware_keycode'):
            msg += ' hw_keycode=%s' % event.hardware_keycode

        device = getattr(event, 'device', None)
        if device:
            device = device.name
            if self.last_device != device:
                self.last_device = device
                self.device_label.set_text(device)

        xtilt = event.get_axis(gdk.AXIS_XTILT)
        ytilt = event.get_axis(gdk.AXIS_YTILT)
        if xtilt is not None or ytilt is not None:
            self.tilt_label.set_text('%+4.4f / %+4.4f' % (xtilt, ytilt))

        return msg

    def report(self, msg):
        print msg
        self.log.append(msg)
        self.log = self.log[-28:]
        buf = self.tv.get_buffer()
        buf.set_text('\n'.join(self.log))

    def event_cb(self, widget, event):
        if event.type == gdk.EXPOSE:
            return False
        msg = self.event2str(event)
        if event.type == gdk.MOTION_NOTIFY:
            self.motion_counter += 1
            if self.unreported_motion:
                self.suppressed += 1
            else:
                self.suppressed = 0
                self.report(msg)
            self.unreported_motion = msg
        else:
            if self.unreported_motion:
                if self.suppressed > 0:
                    self.report('...      MOTION_NOTIFY %d events suppressed' % self.suppressed)
                    self.report(self.unreported_motion)
                self.unreported_motion = None
            self.report(msg)
        return False

    def map_cb(self, *trash):
        if self.initialized:
            return
        print 'Event statistics enabled.'
        self.initialized = True
        #self.app.doc.tdw.connect("event", self.event_cb)
        self.app.drawWindow.connect("event", self.event_cb)

