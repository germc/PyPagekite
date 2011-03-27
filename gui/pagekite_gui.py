#!/usr/bin/env python
import threading
import webbrowser
import wx

import pagekite


class DemoTaskBarIcon(wx.TaskBarIcon):
  TBMENU_RESTORE = wx.NewId()
  TBMENU_RESTART = wx.NewId()
  TBMENU_CONSOLE = wx.NewId()
  TBMENU_CLOSE   = wx.NewId()
  TBMENU_CHANGE  = wx.NewId()
  TBMENU_REMOVE  = wx.NewId()

  def __init__(self, frame):
    wx.TaskBarIcon.__init__(self)
    self.frame = frame
    self.consoleMenuItem = None

    # Set the image
    icon = self.MakeIcon(wx.Image('pk-logo-127.png', wx.BITMAP_TYPE_PNG))
    self.SetIcon(icon, "Click to examine your pagekites")
    self.imgidx = 1

    # bind some events
    self.Bind(wx.EVT_TASKBAR_LEFT_UP, self.OnTaskBarActivate)
#   self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
    self.Bind(wx.EVT_MENU, self.OnTaskBarConsole, id=self.TBMENU_CONSOLE)
    self.Bind(wx.EVT_MENU, self.OnTaskBarRestart, id=self.TBMENU_RESTART)
    self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
    self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)

  def CreatePopupMenu(self):
    """
    This method is called by the base class when it needs to popup
    the menu for the default EVT_RIGHT_DOWN event.  Just create
    the menu how you want it and return it from this function,
    the base class takes care of the rest.
    """
    menu = wx.Menu()
#   menu.Append(self.TBMENU_RESTORE, "Restore Pagekite")
    self.consoleMenuItem = menu.Append(self.TBMENU_CONSOLE, "Control Panel")
    menu.AppendSeparator()
    menu.Append(self.TBMENU_RESTART, "Restart")
    menu.Append(self.TBMENU_CLOSE,   "Quit")
    return menu

  def MakeIcon(self, img):
    """
    The various platforms have different requirements for the
    icon size...
    """
    if "wxMSW" in wx.PlatformInfo:
      img = img.Scale(16, 16, wx.IMAGE_QUALITY_HIGH)
    elif "wxGTK" in wx.PlatformInfo:
      img = img.Scale(22, 22, wx.IMAGE_QUALITY_HIGH)
    # wxMac can be any size upto 128x128, so leave the source img alone....
    icon = wx.IconFromBitmap(img.ConvertToBitmap())
    return icon

  def OnTaskBarActivate(self, evt):
    if self.frame.IsIconized():
      self.frame.Iconize(False)
    if not self.frame.IsShown():
      self.frame.Show(True)
    self.frame.Raise()

  def OnTaskBarRestart(self, evt):
    self.frame.pagekite.restart()

  def OnTaskBarConsole(self, evt):
    if self.frame and self.frame.pagekite and self.frame.pagekite.pk.ui_httpd:
      try:
        webbrowser.open_new('http://%s:%s/' % self.frame.pagekite.pk.ui_sspec)
      except webbrowser.Error, e:
        wx.MessageBox('Error: %s' % e,
                      caption='Error', style=wx.OK | wx.CENTRE)
    else:
      wx.MessageBox('The console is disabled',
                    caption='Oops!', style=wx.OK | wx.CENTRE)

  def OnTaskBarClose(self, evt):
    wx.CallAfter(self.frame.Close)


class PageKiteThread(threading.Thread):
  def __init__(self, frame):
    threading.Thread.__init__(self)
    self.frame = frame
    self.alive = False
    self.pk = None

  def Configure(self, pk):
    self.pk = pk
    if not self.alive: raise KeyboardInterrupt('Quit')
    rv = pagekite.Configure(pk)
    return rv

  def run(self):
    self.alive = True
    return pagekite.Main(pagekite.PageKite, lambda pk: self.Configure(pk))

  def restart(self):
    if self.pk:
      self.pk.looping = False
      self.pk = None

  def quit(self):
    self.frame = None
    if self.pk: self.pk.looping = self.alive = False


class MainFrame(wx.Frame):
  def __init__(self, parent):
    wx.Frame.__init__(self, parent, title="Pagekite")
    self.tbicon = DemoTaskBarIcon(self)
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    self.pagekite = PageKiteThread(self)
    self.pagekite.start()

  def OnCloseWindow(self, evt):
    self.pagekite.quit()
    self.tbicon.Destroy()
    evt.Skip()


if __name__ == '__main__':
  app = wx.App(redirect=False)
  frame = MainFrame(None)
  app.MainLoop()
