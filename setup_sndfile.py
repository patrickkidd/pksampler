import os.path
from distutils.core import setup, Extension


sndfile_sources = ["sndfile.c", "debug.c"]
sndfile_sources = [os.path.join('vendor/dsptools', sfile) for sfile in sndfile_sources]


formats_sources = ["formats.c"]
formats_sources = [os.path.join('vendor/dsptools', sfile) for sfile in formats_sources]
ext_modules = [ Extension( "formats",
                           sources=formats_sources
                           ),
                Extension( "sndfile",
                           sources=sndfile_sources, 
                           libraries = ["sndfile"],
                           ),
                ]

if __name__ == '__main__':
    setup(name="dsptools",
          version="0.4",
          url="http://arrowtheory.com/",
          author="Simon Burton",
          author_email="simon@arrowtheory.com",
          packages = ["dsptools"],
          package_dir = { "dsptools":"vendor/dsptools" },
          ext_package = "dsptools",
          ext_modules = ext_modules,
          )
