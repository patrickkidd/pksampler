/** RtMidiOut **/

typedef struct {
  PyObject_HEAD
  /* Type-specific fields go here. */
  RtMidiOut *rtmidi;
} MidiOut;


static void
MidiOut_dealloc(MidiOut *self)
{
  delete self->rtmidi;
  self->ob_type->tp_free((PyObject *) self);
}


static PyObject *
MidiOut_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  MidiOut *self;
  self = (MidiOut *) type->tp_alloc(type, 0);
  if(self != NULL) 
    {
      try
        {
          self->rtmidi = new RtMidiOut;
        }
      catch(RtError &error)
        {
          PyErr_Format(RtMidiError, error.getMessageString());
          Py_DECREF(self);
          return NULL;
        }
    }
  return (PyObject *) self;
}

static int
MidiOut_init(MidiOut *self, PyObject *args, PyObject *kwds)
{
  return 0;
}


static PyObject *
MidiOut_openPort(MidiOut *self, PyObject *args)
{
  int port = 0;

  if(!PyArg_ParseTuple(args, "|i", &port))
    return NULL;

  try
    {
      self->rtmidi->openPort(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
MidiOut_openVirtualPort(MidiOut *self, PyObject *args)
{
  char *name = NULL;

  if(!PyArg_ParseTuple(args, "|s", &name))
    return NULL;

  if(name == NULL)
    {
      try
        {
          self->rtmidi->openVirtualPort();
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }
  else
    {
      try
        {
          self->rtmidi->openVirtualPort(name);
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
MidiOut_closePort(MidiOut *self, PyObject *args)
{
  self->rtmidi->closePort();
  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
MidiOut_getPortCount(MidiOut *self, PyObject *args)
{
  return Py_BuildValue("i", self->rtmidi->getPortCount());
}


static PyObject *
MidiOut_getPortName(MidiOut *self, PyObject *args)
{
  int port;
  std::string name;

  if(!PyArg_ParseTuple(args, "i", &port))
    return NULL;

  try
    {
      name = self->rtmidi->getPortName(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  return Py_BuildValue("s", name.c_str());
}


static PyObject *
MidiOut_sendMessage(MidiOut *self, PyObject *args)
{
  unsigned char b1, b2, b3;
  std::vector<unsigned char> message;
  
  if(!PyArg_ParseTuple(args, "BBB", &b1, &b2, &b3))
    return NULL;

  message.push_back(b1);
  message.push_back(b2);
  message.push_back(b3);

  try
    {
      self->rtmidi->sendMessage(&message);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());      
    }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef MidiOut_methods[] = {
  {"openPort", (PyCFunction) MidiOut_openPort, METH_VARARGS,
   "Open a MIDI input connection."},

  {"openVirtualPort", (PyCFunction) MidiIn_openVirtualPort, METH_VARARGS,
   "Create a virtual input port, with optional name, to allow software "
   "connections (OS X and ALSA only)."},

  {"closePort", (PyCFunction) MidiOut_closePort, METH_NOARGS,
   "Close an open MIDI connection (if one exists)."},

  {"getPortCount", (PyCFunction) MidiOut_getPortCount, METH_NOARGS,
   "Return the number of available MIDI output ports."},

  {"getPortName", (PyCFunction) MidiOut_getPortName, METH_VARARGS,
   "Return a string identifier for the specified MIDI port type and number."},

  {"sendMessage", (PyCFunction) MidiOut_sendMessage, METH_VARARGS,
   "Immediately send a single message out an open MIDI output port."},

  {NULL}
};


static PyTypeObject MidiOut_type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "midi.RtMidiOut",             /*tp_name*/
    sizeof(MidiOut), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) MidiOut_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "Midi output device",           /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    0,               /* tp_iter */
    0,               /* tp_iternext */
    MidiOut_methods,             /* tp_methods */
    0,              /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)MidiOut_init,      /* tp_init */
    0,                         /* tp_alloc */
    MidiOut_new,                 /* tp_new */
};
