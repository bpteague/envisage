""" This code has been inspired from the IPython repository

https://github.com/ipython/ipython/blob/2.x/examples/Embedding/internal_ipkernel.py

"""

from IPython.lib.kernel import connect_qtconsole
from IPython.kernel.zmq.kernelapp import IPKernelApp


def mpl_kernel(gui_backend):
    """ Launch and return an IPython kernel with matplotlib support.

    Parameters
    ----------
    gui_backend -- string or None
      The GUI mode used to initialize the matplotlib mode. For options, see
      the `ipython --matplotlib` help pages. If None, the kernel is initialized
      without GUI support.
    """

    kernel = IPKernelApp.instance()

    argv = ['python']
    if gui_backend is not None:
        argv.append(gui_backend)
    kernel.initialize(argv)

    return kernel


class InternalIPKernel(object):
    """ Represents an IPython kernel and the consoles attached to it.
    """
    def __init__(self):
        # The IPython kernel.
        self.ipkernel = None
        # A list of connected Qt consoles.
        self.consoles = []

    def init_ipkernel(self, gui_backend):
        """ Initialize the IPython kernel.

        Parameters
        ----------
        gui_backend -- string
          The GUI mode used to initialize the matplotlib mode. For options, see
          the `ipython --matplotlib` help pages.
        """
        # Start IPython kernel with GUI event loop and mpl support
        self.ipkernel = mpl_kernel(gui_backend)

        # This application will also act on the shell user namespace
        self.namespace = self.ipkernel.shell.user_ns

    def new_qt_console(self, evt=None):
        """ Start a new qtconsole connected to our kernel. """
        return connect_qtconsole(
            self.ipkernel.connection_file, profile=self.ipkernel.profile
        )

    def cleanup_consoles(self, evt=None):
        """ Kill all existing consoles. """
        for c in self.consoles:
            c.kill()
        self.consoles = []

    def shutdown(self):
        """ Shutdown the kernel.

        Existing IPython consoles are killed first.
        """
        if self.ipkernel is not None:
            self.cleanup_consoles()
            self.ipkernel.shell.exit_now = True
            self.ipkernel = None
