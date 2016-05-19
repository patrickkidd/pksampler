#   Copyright (C) 2006 by Patrick Stinson                                 
#   patrickkidd@gmail.com                                                   
#                                                                         
#   This program is free software; you can redistribute it and/or modify  
#   it under the terms of the GNU General Public License as published by  
#   the Free Software Foundation; either version 2 of the License, or     
#   (at your option) any later version.                                   
#                                                                         
#   This program is distributed in the hope that it will be useful,       
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
#   GNU General Public License for more details.                          
#                                                                         
#   You should have received a copy of the GNU General Public License     
#   along with this program; if not, write to the                         
#   Free Software Foundation, Inc.,                                       
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.  
#
"""
Manage buffer id's.
"""

import pool


class Loader:
    """ manage buffer ids for playing synths. """
    # rename to something buffer related?
    def __init__(self, controller, verbose=False):
        self.controller = controller
        self.buffer_pool = pool.IntPool(0)
        self.verbose = verbose
        self.controller.sendMsg('/notify', 1)

    def load(self, fpath):
        """ return a buffer id """
        bid = self.buffer_pool.get()
        self.controller.sendMsg('/b_allocRead', bid, fpath)
        return bid

    def unload(self, bid):
        self.controller.sendMsg('/b_free', bid)
        self.controller.receive('/done', '/fail')
        self.buffer_pool.recycle(bid)
