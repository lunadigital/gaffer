##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import unittest
import threading
import time

import IECore

import Gaffer
import GafferTest

class NodeTest( unittest.TestCase ) :

	def testParenting( self ) :
	
		c = Gaffer.GraphComponent()
		n = Gaffer.Node()
		self.assertEqual( n.acceptsParent( c ), False )
		self.assertRaises( RuntimeError, c.addChild, n )
	
		n2 = Gaffer.Node()
		self.assertEqual( n.acceptsParent( n2 ), True )
		n2.addChild( n )
	
		p = Gaffer.Plug()
		self.assert_( n.acceptsChild( p ) )
		self.assert_( not n.acceptsParent( p ) )
		n.addChild( p )
		self.assert_( p.parent().isSame( n ) )
	
	def testNaming( self ) :
	
		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )	
	
	def testOperation( self ) :
		
		n1 = GafferTest.AddNode()
		n1["sum"].getValue()
		
		dirtiedPlugs = GafferTest.CapturingSlot( n1.plugDirtiedSignal() )
		setPlugs = GafferTest.CapturingSlot( n1.plugSetSignal() )	
		
		n1["op1"].setValue( 2 )
		self.assertEqual( len( setPlugs ), 1 )
		self.assertEqual( len( dirtiedPlugs ), 1 )
		self.assertEqual( setPlugs[0][0].fullName(), "AddNode.op1" )
		self.assertEqual( dirtiedPlugs[0][0].fullName(), "AddNode.sum" )
		
		n1["op2"].setValue( 3 )
		self.assertEqual( len( setPlugs ), 2 )
		self.assertEqual( setPlugs[1][0].fullName(), "AddNode.op2" )
		# the dirty callback shouldn't have been triggered this time,
		# as the plug was already dirty.
		## \todo Reintroduce me
		#self.assertEqual( len( dirtiedPlugs ), 1 )
		
		del dirtiedPlugs[:]
		del setPlugs[:]
		
		# plug set or dirty signals are not emitted during computation
		self.assertEqual( n1.getChild("sum").getValue(), 5 )
		self.assertEqual( len( setPlugs ), 0 )
		self.assertEqual( len( dirtiedPlugs ), 0 )
		
		# connect another add node onto the output of this one
		
		n2 = GafferTest.AddNode( "Add2" )
		
		dirtiedPlugs2 = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )
		setPlugs2 = GafferTest.CapturingSlot( n2.plugSetSignal() )	
		
		n2["op1"].setInput( n1["sum"] )
		# connecting a plug doesn't set the value of the input plug
		# immediately - the value is transferred only upon request.
		self.assertEqual( len( setPlugs2 ), 0 )
		self.assertEqual( len( dirtiedPlugs2 ), 2 )
		self.assertEqual( dirtiedPlugs2[0][0].fullName(), "Add2.op1" )
		self.assertEqual( dirtiedPlugs2[1][0].fullName(), "Add2.sum" )
		
		del dirtiedPlugs2[:]
		del setPlugs2[:]
		
		self.assertEqual( n2["op1"].getValue(), 5 )
		self.assertEqual( n2["sum"].getValue(), 5 )

		# plug set or dirty signals are not emitted during computation
		self.assertEqual( len( setPlugs2 ), 0 )
		self.assertEqual( len( dirtiedPlugs2 ), 0 )
	
	def testScriptNode( self ) :
	
		n = Gaffer.Node()
		n2 = Gaffer.Node()
		self.assertEqual( n.scriptNode(), None )
		self.assertEqual( n2.scriptNode(), None )
		
		sn = Gaffer.ScriptNode()
		
		sn.addChild( n )
		n.addChild( n2 )
		
		self.assert_( n.scriptNode().isSame( sn ) )		
		self.assert_( n2.scriptNode().isSame( sn ) )		
	
	def testDirtyOfInputsWithConnections( self ) :
	
		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )
		
		dirtied = GafferTest.CapturingSlot( n1.plugDirtiedSignal(), n2.plugDirtiedSignal() )
		
		n2["op1"].setInput( n1["sum"] )
		self.assertEqual( len( dirtied ), 2 )
		self.failUnless( dirtied[0][0].isSame( n2["op1"] ) )
		self.failUnless( dirtied[1][0].isSame( n2["sum"] ) )

		del dirtied[:]
		n1["op1"].setValue( 10 )
		self.assertEqual( len( dirtied ), 3 )
		self.failUnless( dirtied[0][0].isSame( n1["sum"] ) )
		self.failUnless( dirtied[1][0].isSame( n2["op1"] ) )
		self.failUnless( dirtied[2][0].isSame( n2["sum"] ) )
		
		self.assertEqual( n2.getChild( "sum" ).getValue(), 10 )
	
	def testDirtyPlugComputesSameValueAsBefore( self ) :
	
		n1 = GafferTest.AddNode( "N1" )
		n2 = GafferTest.AddNode( "N2" )
		
		n2.getChild( "op1" ).setInput( n1.getChild( "sum" ) )
				
		n1.getChild( "op1" ).setValue( 1 )
		n1.getChild( "op2" ).setValue( -1 )
		
		self.assertEqual( n2.getChild( "sum" ).getValue(), 0 )
	
	def testExtendedConstructor( self ) :
		
		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )
		
		n = Gaffer.Node( "a" )
		self.assertEqual( n.getName(), "a" )
				
		self.assertRaises( Exception, Gaffer.Node, "too", "many" )
		
		n = GafferTest.AddNode( "hello", inputs = { "op1" : 1, "op2" : 2 } )
		self.assertEqual( n.getName(), "hello" )
		self.assertEqual( n["op1"].getValue(), 1 )
		self.assertEqual( n["op2"].getValue(), 2 )
		
		n2 = GafferTest.AddNode( "goodbye", inputs = { "op1" : n["sum"] } )
		self.assert_( n2["op1"].getInput().isSame( n["sum"] ) )
	
	def testOutputsDirtyForNewNodes( self ) :
	
		n = GafferTest.AddNode( inputs = { "op1" : 1, "op2" : 2 } )
		self.assertEqual( n["sum"].getValue(), 3 )
	
	def testDynamicPlugSerialisationOrder( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p3"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( n.children()[0].getName(), "p1" )
		self.assertEqual( n.children()[1].getName(), "p2" )
		self.assertEqual( n.children()[2].getName(), "p3" )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"].children()[0].getName(), "p1" )
		self.assertEqual( s["n"].children()[1].getName(), "p2" )
		self.assertEqual( s["n"].children()[2].getName(), "p3" )
	
	def testSerialiseDynamicStringPlugs( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.StringPlug( defaultValue = "default", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( "value" )
		self.assertEqual( n["p1"].getValue(), "value" )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p1"].defaultValue(), "default" )
		self.assertEqual( s["n"]["p1"].getValue(), "value" )
	
	def testSerialiseDynamicBoolPlugs( self ) :
	
		n = Gaffer.Node()
		
		n["p1"] = Gaffer.BoolPlug( defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( False )
		
		s = Gaffer.ScriptNode()
		s["n"] = n
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["n"]["p1"].defaultValue(), True )
		self.assertEqual( s["n"]["p1"].getValue(), False )
		
	def testUnparentingRemovesConnections( self ) :
	
		s = Gaffer.ScriptNode()
		
		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )
		
		s.addChild( n1 )
		s.addChild( n2 )
		
		n2["op1"].setInput( n1["sum"] )
		self.failUnless( n2["op1"].getInput().isSame( n1["sum"] ) )
		
		del s["n2"]
		
		self.assertEqual( n2["op1"].getInput(), None )
		
		s.addChild( n2 )

		n2["op1"].setInput( n1["sum"] )
		self.failUnless( n2["op1"].getInput().isSame( n1["sum"] ) )

		del s["n1"]
		
		self.assertEqual( n2["op1"].getInput(), None )
		
	def testComputeInContext( self ) :
	
		n = GafferTest.FrameNode()
		self.assertEqual( n["output"].getValue(), 1 )
	
		c = Gaffer.Context()
		c.setFrame( 10 )
		
		with c :
			self.assertEqual( n["output"].getValue(), 10 )
	
	def testComputeInThreads( self ) :
	
		n = GafferTest.FrameNode()
		
		def f( frame ) :
		
			c = Gaffer.Context()
			c.setFrame( frame )
			
			with c :
				time.sleep( 0.01 )
				self.assertEqual( n["output"].getValue(), frame )
		
		threads = []
		for i in range( 0, 1000 ) :
		
			t = threading.Thread( target = f, args = ( i, ) )
			t.start()
			threads.append( t )
			
		for t in threads :
			t.join()
			
	def testDirtyNotPropagatedDuringCompute( self ) :
					
		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )
		
		n1["op1"].setValue( 2 )
		n1["op2"].setValue( 3 )
		n2["op1"].setInput( n1["sum"] )
		
		dirtyCapturer = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )
				
		self.assertEqual( n2["sum"].getValue(), 5 )
		
		self.assertEqual( len( dirtyCapturer ), 0 )
	
	def testWrongPlugSet( self ) :
	
		n = GafferTest.BadNode()
		self.assertRaises( RuntimeError, n["out1"].getValue )
	
	def testWrongPlugPulled( self ) :
	
		n = GafferTest.BadNode()
		self.assertRaises( RuntimeError, n["out2"].getValue )
	
	def testPlugNotSet( self ) :
	
		n = GafferTest.BadNode()
		self.assertRaises( RuntimeError, n["out3"].getValue )
		
	def testOverrideAcceptsInput( self ) :
	
		class AcceptsInputTestNode( Gaffer.Node ) :
		
			def __init__( self, name = "AcceptsInputTestNode" ) :
			
				Gaffer.Node.__init__( self, name )
				
				self.addChild( Gaffer.IntPlug( "in" ) )
				self.addChild( Gaffer.IntPlug( "out", Gaffer.Plug.Direction.Out ) )
				
			def acceptsInput( self, plug, inputPlug ) :
			
				return isinstance( inputPlug.node(), AcceptsInputTestNode )
	
		n1 = AcceptsInputTestNode()
		n2 = AcceptsInputTestNode()
		n3 = GafferTest.AddNode()
	
		self.assertEqual( n1["in"].acceptsInput( n2["out"] ), True )
		self.assertEqual( n1["in"].acceptsInput( n3["sum"] ), False )
	
	def testDirtyOnDisconnect( self ) :
	
		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )
		
		n1["op1"].setValue( 2 )
		n1["op2"].setValue( 3 )
		
		dirtied = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )
		set = GafferTest.CapturingSlot( n2.plugSetSignal() )
		n2["op1"].setInput( n1["sum"] )
				
		self.assertEqual( len( set ), 0 )
		self.assertEqual( len( dirtied ), 2 )
		self.failUnless( dirtied[0][0].isSame( n2["op1"] ) )
		self.failUnless( dirtied[1][0].isSame( n2["sum"] ) )

		n2["op1"].setInput( None )
		
		self.assertEqual( len( set ), 1 )
		self.failUnless( set[0][0].isSame( n2["op1"] ) )
		self.assertEqual( len( dirtied ), 3 )
		self.failUnless( dirtied[2][0].isSame( n2["sum"] ) )
	
if __name__ == "__main__":
	unittest.main()
