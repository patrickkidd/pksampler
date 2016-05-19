/** RtMidiIn **/


#ifdef __WINDOWS_MM__
#include "thread.hpp"
#endif


typedef struct {
  PyObject_HEAD
  /* Type-specific fields go here. */
  RtMidiIn *rtmidi;
  
  bool blocking;
  std::queue<midi_message_t> *queue;
#ifdef __WINDOWS_MM__NOT
  HANDLE mutex;
#else
  pthread_mutex_t mutex;
  pthread_cond_t cond;
  pthread_mutex_t cond_mutex;
#endif
} MidiIn;


static void
MidiIn_dealloc(MidiIn *self)
{
  delete self->rtmidi;
#ifdef __WINDOWS_MM__NOT
#else
  pthread_mutex_destroy(&self->mutex);
  pthread_mutex_destroy(&self->cond_mutex);
  pthread_cond_destroy(&self->cond);
  delete self->queue;
#endif
  self->ob_type->tp_free((PyObject *) self);
}


static PyObject *
MidiIn_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  MidiIn *self;
  self = (MidiIn *) type->tp_alloc(type, 0);
  if(self != NULL) 
    {
      try
        {
          self->rtmidi = new RtMidiIn;
        }
      catch(RtError &error)
        {
          PyErr_SetString(RtMidiError, error.getMessageString());
          Py_DECREF(self);
          return NULL;
        }
    }
  return (PyObject *) self;
}

static int
MidiIn_init(MidiIn *self, PyObject *args, PyObject *kwds)
{
#ifdef __WINDOWS_MM__NOT
#else
  // why??
  pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
  pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
  self->mutex = mutex;
  pthread_mutex_init(&self->mutex, NULL);
  self->cond_mutex = mutex;
  pthread_mutex_init(&self->cond_mutex, NULL);  
  self->cond = cond;
  pthread_cond_init(&self->cond, NULL);
#endif
  self->blocking = false;
  self->queue = new std::queue<midi_message_t>;
  return 0;
}


void rtmidi_blocking_cb(double stamp, 
                        std::vector<unsigned char> *bytes,
                        void *userData)
{
  MidiIn *self = (MidiIn *) userData;
  midi_message_t message;

  for(uint i=0; i < bytes->size(); i++)
    message.bytes.push_back((*bytes)[i]);
  message.timestamp = stamp;


#ifdef __WINDOWS_MM__NOT
#else
  // prevent a race condition
  pthread_mutex_lock(&self->mutex);
  self->queue->push(message);
  pthread_mutex_unlock(&self->mutex);
  pthread_cond_broadcast(&self->cond);
#endif
}


static PyObject *
MidiIn_openPort(MidiIn *self, PyObject *args)
{
  int port;
  PyObject *blocking = NULL;

  if(!PyArg_ParseTuple(args, "i|O", &port, &blocking))
    return NULL;

  /*
  if(port == 0)
    return PyErr_Format(RtMidiError, 
			"opening device 0 locks my system, and it may lock yours, too!");
  */
  if(blocking == Py_True)
    {
      self->rtmidi->setCallback(rtmidi_blocking_cb, self);
      self->blocking = true;
    }
  else
    {
      self->blocking = false;
    }

  try
    {
      self->rtmidi->openPort(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_openVirtualPort(MidiIn *self, PyObject *args)
{
  char *name = NULL;
  PyObject *blocking = NULL;

  if(!PyArg_ParseTuple(args, "|sO", &name, &blocking))
    return NULL;

  if(blocking == Py_True)
    {
      self->rtmidi->setCallback(rtmidi_blocking_cb, self);
      self->blocking = true;
    }
  else
    {
      self->blocking = false;
    }

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

  Py_RETURN_NONE;
}


struct cb_pair
{
  PyThreadState *tstate;
  PyObject *ocallback;
};


static PyThreadState *setCallback_tstate;

void rtmidi_GIL_callback(double timeStamp, std::vector<unsigned char> *message,
                void *userData)
{
  PyObject *result;
  PyObject *arglist;
  //PyObject *ocallback = (PyObject *) userData;
  PyObject *ostamp;
  struct cb_pair *cb_data = (struct cb_pair *) userData;

  /************************************/
  PyEval_AcquireThread(cb_data->tstate);
  /************************************/

  arglist = PyTuple_New(message->size()+1);
  if(!arglist)
    goto fail;

  for(uint i=0; i < message->size(); i++)
    {
      PyObject *obyte = Py_BuildValue("B", (*message)[i]);
      if(obyte == NULL)
        goto fail;
      if(PyTuple_SetItem(arglist, i, obyte))
        goto fail;
    }
  
  ostamp = Py_BuildValue("d", timeStamp);
  if(!ostamp)
    goto fail;
  if(PyTuple_SetItem(arglist, message->size(), ostamp))
    goto fail;

  std::cout << "here" << message->size() << std::endl;
  // result = PyEval_CallObject(cb_data->ocallback, arglist);
  goto fail;

  /************************************/
  PyEval_ReleaseThread(cb_data->tstate);
  /************************************/

  if(result == NULL)
    {
      PyGILState_STATE gil_state = PyGILState_Ensure();
      PyErr_Format(RtMidiError, "async exception");
      PyThreadState_SetAsyncExc(setCallback_tstate->thread_id, RtMidiError);
      PyGILState_Release(gil_state);
    }

  Py_XDECREF(arglist);
  return;
      
 fail:
  Py_XDECREF(arglist);
}


static PyObject *
MidiIn_setCallback(MidiIn *self, PyObject *args)
{
  PyObject *ocallback;
  struct cb_pair *cb_data;

  if(!PyArg_ParseTuple(args, "O:setCallback", ocallback))
    return NULL;

  if(!PyCallable_Check(ocallback))
    {
      PyErr_Format(PyExc_TypeError, "parameter must be a callable");
      return NULL;
    }
  
  
  cb_data = (struct cb_pair *) PyMem_Malloc(sizeof(cb_pair));
  //cb_data = (struct cb_pair *) malloc(sizeof(struct cb_pair));
  if(cb_data == NULL)
    {
      PyErr_Format(RtMidiError, "PyMem_Malloc: failed");
      return NULL;
    }

  setCallback_tstate = PyThreadState_Get();
  if(setCallback_tstate == NULL)
    {
      PyErr_Format(RtMidiError, "PyThreadState_Get: failed");
      return NULL;
    }

  cb_data->ocallback = ocallback;
  cb_data->tstate = PyThreadState_New(setCallback_tstate->interp);

  if(cb_data->tstate == NULL)
    {
      PyErr_Format(RtMidiError, "PyThreadState_New: failed");
      return NULL;
    }
  
  Py_XINCREF(ocallback);
  self->rtmidi->setCallback(rtmidi_GIL_callback, cb_data);

  Py_RETURN_NONE;
}



static PyObject *
MidiIn_cancelCallback(MidiIn *self, PyObject *args)
{
  self->rtmidi->cancelCallback();
  
  Py_RETURN_NONE;
}


static PyObject *
MidiIn_closePort(MidiIn *self, PyObject *args)
{
  self->rtmidi->closePort();

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_getPortCount(MidiIn *self, PyObject *args)
{
  return Py_BuildValue("i", self->rtmidi->getPortCount());
}


static PyObject *
MidiIn_getPortName(MidiIn *self, PyObject *args)
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
MidiIn_setQueueSizeLimit(MidiIn *self, PyObject *args)
{
  unsigned int queueSize;

  if(!PyArg_ParseTuple(args, "I", &queueSize))
    return NULL;

  self->rtmidi->setQueueSizeLimit(queueSize);

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_ignoreTypes(MidiIn *self, PyObject *args)
{
  PyObject *omidiSysex = Py_True;
  PyObject *omidiTime = Py_True;
  PyObject *omidiSense = Py_True;

  bool midiSysex;
  bool midiTime;
  bool midiSense;

  if(!PyArg_ParseTuple(args, "|OOO", &omidiSysex, &omidiTime, &omidiSense))
    return NULL;

  midiSysex = (omidiSysex == Py_True);
  midiTime = (omidiTime == Py_True);
  midiSense = (omidiSense = Py_True);

  self->rtmidi->ignoreTypes(midiSysex, midiTime, midiSense);

  Py_RETURN_NONE;
}



/*
int cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, int ms)
{
  struct timeval now;
  struct timespec timeout;

  pthread_mutex_lock(mutex);
  gettimeofday(&now, NULL);
  timeout.tv_sec = now.tv_sec;
  timeout.tv_nsec = now.tv_usec + ms * 1000000;

  return pthread_cond_timedwait(cond, mutex, &timeout);
}
*/

static PyObject *
MidiIn_getMessage(MidiIn *self, PyObject *args)
{
  PyObject *ret;
  double stamp;
  std::vector<unsigned char> message;

  if(self->blocking == false)
    {  
      try
        {
          stamp = self->rtmidi->getMessage( &message );
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }
  else
    {
      int q_sz;
      midi_message_t msg;


      Py_BEGIN_ALLOW_THREADS

#ifdef __WINDOWS_MM__NOT
#else
      pthread_mutex_lock(&self->mutex);
#endif
      q_sz = self->queue->size();
#ifdef __WINDOWS_MM__NOT
#else
      pthread_mutex_unlock(&self->mutex);
#endif

      if(q_sz <= 0)
        {
          //int ret = ETIMEDOUT;
          //          while(ret == ETIMEDOUT && !self->deleted)
          //while(ret == ETIMEDOUT)
#ifdef __WINDOWS_MM__NOT
#else          
          pthread_cond_wait(&self->cond, &self->cond_mutex);
#endif
            //ret = cond_timedwait(&self->cond, &self->mutex, 10);
          /*
          if(self->deleted)
            {
	      Py_RETURN_NONE;
            }
          */
        }
#ifdef __WINDOWS_MM__NOT
#else
      pthread_mutex_lock(&self->mutex);
#endif
      msg = self->queue->front();
      self->queue->pop();
#ifdef __WINDOWS_MM__NOT
#else
      pthread_mutex_unlock(&self->mutex);
#endif

      message = msg.bytes;
      stamp = msg.timestamp;

      Py_END_ALLOW_THREADS;
    }


  if(message.size())
    {
      ret = PyTuple_New(message.size()+1);
      if(ret == NULL)
        goto fail;
      
      for(uint i=0; i < message.size(); i++)
        {
          PyObject *obyte = Py_BuildValue("B", message[i]);
          if(obyte == NULL)
            goto fail;
          if(PyTuple_SetItem(ret, i, obyte))
            goto fail;
        }
            
      PyObject *ostamp = Py_BuildValue("d", stamp);
      if(!ostamp)
        goto fail;
      if(PyTuple_SetItem(ret, message.size(), ostamp))
        goto fail;
    }
  else
    {
      ret = PyTuple_New(0);
      if(ret == NULL)
        goto fail;
    }
  return ret;

 fail:
  Py_XDECREF(ret);
  return NULL;  
}


static PyMethodDef MidiIn_methods[] = {
  {"openPort", (PyCFunction) MidiIn_openPort, METH_VARARGS,
   "Open a MIDI input connection. openPort(port, blocking=False)\n"
   "If the optional blocking parameter is passed getMessage will block until a message is available."},

  {"openVirtualPort", (PyCFunction) MidiIn_openVirtualPort, METH_VARARGS,
   "Create a virtual input port, with optional name, to allow software "
   "connections (OS X and ALSA only)."},

  /*
  {"setCallback", (PyCFunction) MidiIn_setCallback, METH_VARARGS,
   "Set a callback function to be invoked for incoming MIDI messages."},
  */

  {"cancelCallback", (PyCFunction) MidiIn_cancelCallback, METH_NOARGS,
   "Cancel use of the current callback function (if one exists)."},

  {"closePort", (PyCFunction) MidiIn_closePort, METH_NOARGS,
   "Close an open MIDI connection (if one exists)."},

  {"getPortCount", (PyCFunction) MidiIn_getPortCount, METH_NOARGS,
   "Return the number of available MIDI input ports."},

  {"getPortName", (PyCFunction) MidiIn_getPortName, METH_VARARGS,
   "Return a string identifier for the specified MIDI input port number."},

  {"setQueueSizeLimit", (PyCFunction) MidiIn_setQueueSizeLimit, METH_VARARGS,
   "Set the maximum number of MIDI messages to be saved in the queue."},
  
  {"ignoreTypes", (PyCFunction) MidiIn_ignoreTypes, METH_VARARGS,
   "Specify whether certain MIDI message types should be queued or ignored "
   "during input."},
  
  {"getMessage", (PyCFunction) MidiIn_getMessage, METH_NOARGS,
   "Return the data bytes for the next available MIDI message in"
   "the input queue and return the event delta-time in seconds.\n"
   "This method will block if openPort() was called in blocking mode"},

  {NULL}
};


static PyTypeObject MidiIn_type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "midi.RtMidiIn",             /*tp_name*/
    sizeof(MidiIn), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) MidiIn_dealloc,                         /*tp_dealloc*/
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
    "Midi input device",           /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    0,               /* tp_iter */
    0,               /* tp_iternext */
    MidiIn_methods,             /* tp_methods */
    0,              /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)MidiIn_init,      /* tp_init */
    0,                         /* tp_alloc */
    MidiIn_new,                 /* tp_new */
};

