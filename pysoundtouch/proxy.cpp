/***************************************************************************
 *   Copyright (C) 2006 by Patrick Stinson                                 *
 *   patrickkidd@gci.net                                                   *
 *                                                                         *
 *   Permission is hereby granted, free of charge, to any person obtaining *
 *   a copy of this software and associated documentation files (the       *
 *   "Software"), to deal in the Software without restriction, including   *
 *   without limitation the rights to use, copy, modify, merge, publish,   *
 *   distribute, sublicense, and/or sell copies of the Software, and to    *
 *   permit persons to whom the Software is furnished to do so, subject to *
 *   the following conditions:                                             *
 *                                                                         *
 *   The above copyright notice and this permission notice shall be        *
 *   included in all copies or substantial portions of the Software.       *
 *                                                                         *
 *   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,       *
 *   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF    *
 *   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.*
 *   IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR     *
 *   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, *
 *   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR *
 *   OTHER DEALINGS IN THE SOFTWARE.                                       *
 ***************************************************************************/

#include <memory.h>
#include <soundtouch/BPMDetect.h>


#define BUFF_SIZE 1024

extern "C" float soundtouch_proxy_find_bpm(const float *sound, 
                                           int length, 
                                           int samplerate)
{
  int channels = 2;
  const float *cur = sound;
  const float *end = sound + length;
  soundtouch::SAMPLETYPE stage[BUFF_SIZE];
  BPMDetect bpm(2, samplerate);

  int items = BUFF_SIZE;
  while(cur != end)
    {
      if(end - cur < items)
        items = end - cur;

      memcpy(stage, cur, items * sizeof(float));
      cur += items;

      bpm.inputSamples(stage, items / channels);

    }
  return bpm.getBpm();
}
