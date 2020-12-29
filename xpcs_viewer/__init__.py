# from xpcs_viwer.viewer_kernel import Viewer_Kernel
from .viewer import run 
from .viewer_kernel import ViewerKernel
from .xpcs_file import XpcsFile as xf
from . import icons_rc

__all__ = [run, xf, icons_rc]
__version__ = '0.1.0'
__author__ = 'Miaoqi Chu'
__credits__ = 'Argonne National Laboratory'
