#include <Python.h>
#include <queue>
#include "RtMidi.h"

#ifdef __WINDOWS_MM__
typedef unsigned int uint;
#include <windows.h>
#else
#include <pthread.h>
#endif

#ifndef Py_RETURN_NONE
#define Py_RETURN_NONE Py_INCREF(Py_None); return Py_None;
#endif


extern "C" {

static PyObject *RtMidiError;


typedef struct 
{
  std::vector<unsigned char> bytes;
  double timestamp;
} midi_message_t;


#include "rtmidiin.cpp"
#include "rtmidiout.cpp"


static PyMethodDef midi_methods[] = {
    {NULL}  /* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initrtmidi(void) 
{
  PyEval_InitThreads();

  PyObject* module;
  
  if (PyType_Ready(&MidiIn_type) < 0)
    return;
  if (PyType_Ready(&MidiOut_type) < 0)
    return;
  
  module = Py_InitModule3("rtmidi", midi_methods,
			  "RtMidi wrapper.");
  
  Py_INCREF(&MidiIn_type);
  PyModule_AddObject(module, "RtMidiIn", (PyObject *)&MidiIn_type);
  
  Py_INCREF(&MidiOut_type);
  PyModule_AddObject(module, "RtMidiOut", (PyObject *)&MidiOut_type);
  
  RtMidiError = PyErr_NewException("rtmidi.RtError", NULL, NULL);
  Py_INCREF(RtMidiError);
  PyModule_AddObject(module, "RtError", RtMidiError);
}

} // extern "C"
