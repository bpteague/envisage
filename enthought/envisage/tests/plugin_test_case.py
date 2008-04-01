""" Tests for plugins. """


# Standard library imports.
import random, unittest

# Enthought library imports.
from enthought.envisage.api import Application, ExtensionPoint
from enthought.envisage.api import IPluginActivator, Plugin
from enthought.envisage.api import Service
from enthought.traits.api import HasTraits, Instance, Int, Interface, List, Str
from enthought.traits.api import implements


def listener(obj, trait_name, old, new):
    """ A useful trait change handler for testing! """

    listener.obj = obj
    listener.trait_name = trait_name
    listener.old = old
    listener.new = new

    return


class TestApplication(Application):
    """ The type of application used in the tests. """

    id = 'test'

    
class PluginTestCase(unittest.TestCase):
    """ Tests for plugins. """

    ###########################################################################
    # 'TestCase' interface.
    ###########################################################################

    def setUp(self):
        """ Prepares the test fixture before each test method is called. """

        return

    def tearDown(self):
        """ Called immediately after each test method has been called. """
        
        return
    
    ###########################################################################
    # Tests.
    ###########################################################################

    def test_id_policy(self):
        """ id policy """

        # If no Id or name is specified then use 'module_name.class_name'.
        p = Plugin()
        self.assertEqual('enthought.envisage.plugin.Plugin', p.id)

        # If no Id is specified, but a name is then id == name.
        p = Plugin(name='fred')
        self.assertEqual('fred', p.id)

        # If an Id is specified make sure we use it!
        p = Plugin(id='wilma')
        self.assertEqual('wilma', p.id)

        p = Plugin(name='fred', id='wilma')
        self.assertEqual('wilma', p.id)

        return
    
    def test_plugin_activator(self):
        """ plugin activator. """

        class NullPluginActivator(HasTraits):
            """ A plugin activator that does nothing! """

            implements(IPluginActivator)
            
            def start_plugin(self, plugin):
                """ Start a plugin. """

                self.started = plugin

                return
            
            def stop_plugin(self, plugin):
                """ Stop a plugin. """
                
                self.stopped = plugin

                return

        class PluginA(Plugin):
            id = 'A'

        class PluginB(Plugin):
            id = 'B'

        plugin_activator = NullPluginActivator()

        a = PluginA(activator=plugin_activator)
        b = PluginB()

        application = TestApplication(plugins=[a, b])
        application.start()

        # Make sure A's plugin activator was called.
        self.assertEqual(a, plugin_activator.started)

        # Stop the application.
        application.stop()

        # Make sure A's plugin activator was called.
        self.assertEqual(a, plugin_activator.stopped)

        return
    
    def test_service_trait_type(self):
        """ service trait type"""

        class Foo(HasTraits):
            pass

        class PluginA(Plugin):
            id = 'A'
            foo = Instance(Foo, (), service=True)

        class PluginB(Plugin):
            id = 'B'
            foo = Service(Foo)

        a = PluginA()
        b = PluginB()
        
        application = TestApplication(plugins=[a, b])
        application.start()

        # Make sure the services were registered.
        self.assertEqual(a.foo, b.foo)

        # Stop the application.
        application.stop()

        # Make sure the service was unregistered.
        self.assertEqual(None, b.foo)

        # You can't set service traits!
        self.failUnlessRaises(SystemError, setattr, b, 'foo', 'bogus')
        
        return

    def test_service(self):
        """ service """

        class Foo(HasTraits):
            pass

        class Bar(HasTraits):
            pass

        class Baz(HasTraits):
            pass
        
        class PluginA(Plugin):
            id = 'A'
            foo = Instance(Foo, (), service=True)
            bar = Instance(Bar, (), service=True)
            baz = Instance(Baz, (), service=True)

        a = PluginA()

        application = TestApplication(plugins=[a])
        application.start()

        # Make sure the services were registered.
        self.assertNotEqual(None, application.get_service(Foo))
        self.assertEqual(a.foo, application.get_service(Foo))

        self.assertNotEqual(None, application.get_service(Bar))
        self.assertEqual(a.bar, application.get_service(Bar))

        self.assertNotEqual(None, application.get_service(Baz))
        self.assertEqual(a.baz, application.get_service(Baz))

        application.stop()

        # Make sure the service was unregistered.
        self.assertEqual(None, application.get_service(Foo))
        self.assertEqual(None, application.get_service(Bar))
        self.assertEqual(None, application.get_service(Baz))

        return

    def test_service_protocol(self):
        """ service protocol """

        class IFoo(Interface):
            pass

        class IBar(Interface):
            pass
        
        class Foo(HasTraits):
            implements(IFoo, IBar)

        class PluginA(Plugin):
            id = 'A'
            foo = Instance(Foo, (), service=True, service_protocol=IBar)
            
        a = PluginA()
        
        application = TestApplication(plugins=[a])
        application.start()

        # Make sure the service was registered with the 'IBar' protocol.
        self.assertNotEqual(None, application.get_service(IBar))
        self.assertEqual(a.foo, application.get_service(IBar))

        application.stop()

        # Make sure the service was unregistered.
        self.assertEqual(None, application.get_service(IBar))

        return

    def test_multiple_trait_contributions(self):
        """ multiple trait contributions """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='x')

        class PluginB(Plugin):
            id = 'B'

            x  = List([1, 2, 3], extension_point='x')
            y  = List([4, 5, 6], extension_point='x')

        a = PluginA()
        b = PluginB()

        application = TestApplication(plugins=[a, b])

        # We should get an error because the plugin has multiple traits
        # contributing to the same extension point.
        self.failUnlessRaises(ValueError, application.get_extensions, 'x')

        return

    def test_exception_in_trait_contribution(self):
        """ exception in trait contribution """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='x')

        class PluginB(Plugin):
            id = 'B'

            x  = List(extension_point='x')

            def _x_default(self):
                """ Trait initializer. """

                raise 1/0

        a = PluginA()
        b = PluginB()

        application = TestApplication(plugins=[a, b])

        # We should get an when we try to get the contributions to the
        # extension point.
        self.failUnlessRaises(
            ZeroDivisionError, application.get_extensions, 'x'
        )

        return

    def test_contributes_to(self):
        """ contributes to """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='x')

        class PluginB(Plugin):
            id = 'B'
            x  = List([1, 2, 3], contributes_to='x')

        a = PluginA()
        b = PluginB()

        application = TestApplication(plugins=[a, b])

        # We should get an error because the plugin has multiple traits
        # contributing to the same extension point.
        self.assertEqual([1, 2, 3], application.get_extensions('x'))

        return

    def test_multiple_trait_contributions_with_contributes_to(self):
        """ multiple trait contributions with contributes to """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='x')

        class PluginB(Plugin):
            id = 'B'

            x  = List([1, 2, 3], contributes_to='x')
            y  = List([4, 5, 6], contributes_to='x')

        a = PluginA()
        b = PluginB()

        application = TestApplication(plugins=[a, b])

        # We should get an error because the plugin has multiple traits
        # contributing to the same extension point.
        self.failUnlessRaises(ValueError, application.get_extensions, 'x')

        return

    def test_multiple_trait_contributions_with_mixed_metadata(self):
        """ multiple trait contributions with mixed_metadata """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='x')

        class PluginB(Plugin):
            id = 'B'

            x  = List([1, 2, 3], extension_point='x')
            y  = List([4, 5, 6], contributes_to='x')

        a = PluginA()
        b = PluginB()

        application = TestApplication(plugins=[a, b])

        # We should get an error because the plugin has multiple traits
        # contributing to the same extension point.
        self.failUnlessRaises(ValueError, application.get_extensions, 'x')

        return

    def test_add_plugins_to_empty_application(self):
        """ add plugins to empty application """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List(Int), id='x')
            
            def _x_items_changed(self, event):
                self.added   = event.added
                self.removed = event.removed

                return

        class PluginB(Plugin):
            id = 'B'
            x  = List(Int, [1, 2, 3], contributes_to='x')

        class PluginC(Plugin):
            id = 'C'
            x  = List(Int, [4, 5, 6], contributes_to='x')

        a = PluginA()
        b = PluginB()
        c = PluginC()
        
        # Create an empty application.
        application = TestApplication()
        application.start()

        # Add the plugin that offers the extension point. 
        application.add_plugin(a)

        #######################################################################
        # fixme: Currently, we connect up extension point traits when the
        # plugin is started. Is this right? Should be start plugins by default
        # when we add them (and maybe have the ability to add a plugin without
        # starting it?).
        #
        # I think we should start the plugin, otherwise you have the wierdness
        # that the extension contributed by the plugin are available after
        # the call to 'add_plugin', but the plugin isn't started?!?
        #######################################################################

        application.start_plugin(a)

        #######################################################################
        # fixme: Currently, we only fire changed events if an extension point
        # has already been accessed! Is this right?
        #######################################################################

        self.assertEqual([], a.x)

        # Add a plugin that contributes to the extension point.
        application.add_plugin(b)

        # Make sure that we pick up B's extensions and that the appropriate
        # trait event was fired.
        self.assertEqual([1, 2, 3], a.x)
        self.assertEqual([1, 2, 3], a.added)

        # Add another plugin that contributes to the extension point.
        application.add_plugin(c)

        self.assertEqual([1, 2, 3, 4, 5, 6], a.x)
        self.assertEqual([4, 5, 6], a.added)

        # Remove the first contributing plugin.
        application.remove_plugin(b)

        self.assertEqual([4, 5, 6], a.x)
        self.assertEqual([1, 2, 3], a.removed)

        # Remove the second contributing plugin.
        application.remove_plugin(c)

        self.assertEqual([], a.x)
        self.assertEqual([4, 5, 6], a.removed)

        return


# Entry point for stand-alone testing.
if __name__ == '__main__':
    unittest.main()

#### EOF ######################################################################
