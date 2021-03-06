import wx

import sys
import os
import time
import threading
import math

PPRZ_HOME = os.getenv("PAPARAZZI_HOME")
sys.path.append(PPRZ_HOME + "/sw/lib/python")

import messages_tool

WIDTH = 450
LABEL_WIDTH = 166
DATA_WIDTH = 100
HEIGHT = 800
BORDER = 1

class MessagesFrame(wx.Frame):
  def message_recv(self, ac_id, name, values):
    if self.aircrafts.has_key(ac_id):
      if self.aircrafts[ac_id].messages.has_key(name):
        if time.time() - self.aircrafts[ac_id].messages[name].last_seen < 0.2:
          return

    wx.CallAfter(self.gui_update, ac_id, name, values)

  def find_page(self, book, name):
    if book.GetPageCount() < 1:
      return 0
    start = 0
    end = book.GetPageCount()

    while (start < end):
      if book.GetPageText(start) > name:
        return start
      start = start + 1

    return start

  def update_leds(self):
    wx.CallAfter(self.update_leds_real)

  def update_leds_real(self):
    for ac_id in self.aircrafts:
      aircraft = self.aircrafts[ac_id]
      for msg_str in aircraft.messages:
        message = aircraft.messages[msg_str]
        if message.last_seen + 0.2 < time.time():
          aircraft.messages_book.SetPageImage(message.index, 0)

    self.timer = threading.Timer(0.1, self.update_leds)
    self.timer.start()

  def setup_image_list(self, notebook):
    imageList = wx.ImageList(24,24)

    image = wx.Image(PPRZ_HOME + "/data/pictures/gray_led24.png")
    bitmap = wx.BitmapFromImage(image)
    imageList.Add(bitmap)

    image = wx.Image(PPRZ_HOME + "/data/pictures/green_led24.png")
    bitmap = wx.BitmapFromImage(image)
    imageList.Add(bitmap)

    notebook.AssignImageList(imageList)

  def add_new_aircraft(self, ac_id):
      self.aircrafts[ac_id] = messages_tool.Aircraft(ac_id)
      ac_panel = wx.Panel(self.notebook, -1)
      self.notebook.AddPage(ac_panel, str(ac_id))
      messages_book = wx.Notebook(ac_panel, style=wx.NB_LEFT)
      self.setup_image_list(messages_book)
      sizer = wx.BoxSizer(wx.VERTICAL)
      sizer.Add(messages_book, 1, wx.EXPAND)
      ac_panel.SetSizer(sizer)
      sizer.Layout()
      self.aircrafts[ac_id].messages_book = messages_book

  def add_new_message(self, aircraft, name):
      messages_book = aircraft.messages_book
      aircraft.messages[name] = messages_tool.Message("telemetry", name)
      field_panel = wx.Panel(messages_book)
      grid_sizer = wx.FlexGridSizer(len(aircraft.messages[name].field_names), 2)

      index = self.find_page(messages_book, name)
      messages_book.InsertPage(index, field_panel, name, imageId = 1)
      aircraft.messages[name].index = index

      # update indexes of pages which are to be moved
      for message_name in aircraft.messages:
          aircraft.messages[message_name].index = self.find_page(messages_book, message_name)

      for field_name in aircraft.messages[name].field_names:
        name_text = wx.StaticText(field_panel, -1, field_name)
        size = name_text.GetSize()
        size.x = LABEL_WIDTH
        name_text.SetMinSize(size)
        grid_sizer.Add(name_text, 1, wx.ALL, BORDER)
        value_control = wx.StaticText(field_panel, -1, "42", style=wx.ST_NO_AUTORESIZE)
        size = value_control.GetSize()
        size.x = LABEL_WIDTH
        value_control.SetMinSize(size)
        grid_sizer.Add(value_control, 1, wx.ALL, BORDER)
        aircraft.messages[name].field_controls.append(value_control)
      field_panel.SetAutoLayout(True)
      field_panel.SetSizer(grid_sizer)
      field_panel.Layout()

  def gui_update(self, ac_id, name, values):
    if not self.aircrafts.has_key(ac_id):
      self.add_new_aircraft(ac_id)

    aircraft = self.aircrafts[ac_id]

    if not aircraft.messages.has_key(name):
      self.add_new_message(aircraft,  name)

    aircraft.messages_book.SetPageImage(aircraft.messages[name].index, 1)
    self.aircrafts[ac_id].messages[name].last_seen = time.time()

    for index in range(0, len(values)):
      aircraft.messages[name].field_controls[index].SetLabel(values[index])

  def __init__(self):
    wx.Frame.__init__(self, id=-1, parent=None, name=u'MessagesFrame', size=wx.Size(WIDTH, HEIGHT), style=wx.DEFAULT_FRAME_STYLE, title=u'Messages')
    self.notebook = wx.Notebook(self)
    self.aircrafts = {}

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    sizer.Add(self.notebook, 1, wx.EXPAND)
    self.SetSizer(sizer)
    sizer.Layout()
    self.timer = threading.Timer(0.1, self.update_leds)
    self.timer.start()
    self.interface = messages_tool.IvyMessagesInterface(self.message_recv)
