##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

import os
import unittest

import GafferUI

class CollapsibleTest( unittest.TestCase ) :

	def testConstructor( self ) :
		
		b = GafferUI.Button( "Hide Me" )
		c = GafferUI.Collapsible( child = b, collapsed=True )
	
		self.failUnless( c.getChild() is b )
		self.assertEqual( c.getCollapsed(), True )

	def testSetCollapsed( self ) :
	
		c = GafferUI.Collapsible( collapsed=True )
		
		self.assertEqual( c.getCollapsed(), True )
		c.setCollapsed( False )	
		self.assertEqual( c.getCollapsed(), False )
	
	def testStateChangedSignal( self ) :
	
		self.__states = []
		def stateChanged( widget ) :
		
			self.__states.append( widget.getCollapsed( ) )
			
		c = GafferUI.Collapsible( collapsed=True )
		stateChangedConnection = c.stateChangedSignal().connect( stateChanged )
		
		c.setCollapsed( False )
		self.assertEqual( self.__states, [ False ] )
		
		c.setCollapsed( False ) # shouldn't trigger as state is the same
		self.assertEqual( self.__states, [ False ] )
		
		c.setCollapsed( True )
		self.assertEqual( self.__states, [ False, True ] )
	
	def testCornerWidget( self ) :
	
		c = GafferUI.Collapsible( collapsed = True )
		self.assertEqual( c.getCornerWidget(), None )
		
		b1 = GafferUI.Button()
		self.assertEqual( b1.parent(), None )
		
		b2 = GafferUI.Button()
		self.assertEqual( b1.parent(), None )
		
		c.setCornerWidget( b1 )
		self.failUnless( c.getCornerWidget() is b1 )
		self.failUnless( b1.parent() is c )
		
		c.setCornerWidget( None )
		self.failUnless( c.getCornerWidget() is None )
		self.failUnless( b1.parent() is None )
		
		c.setCornerWidget( b1 )
		self.failUnless( c.getCornerWidget() is b1 )
		self.failUnless( b1.parent() is c )
		
		c.setCornerWidget( b2 )
		self.failUnless( c.getCornerWidget() is b2 )
		self.failUnless( b2.parent() is c )
		self.failUnless( b1.parent() is None )
		
		c.removeChild( b2 )
		self.failUnless( c.getCornerWidget() is None )
		self.failUnless( b2.parent() is None )
		
if __name__ == "__main__":
	unittest.main()
	
