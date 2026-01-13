"""
Workaround for pydub on Python 3.13 where audioop was removed.
This makes pydub's bundled pyaudioop available as a top-level module.
Must be imported BEFORE pydub.
"""
import sys
import os
import importlib.util

# Find pydub package path without importing it
try:
    import site
    # Look for pydub in site-packages
    for site_packages in site.getsitepackages():
        pydub_path = os.path.join(site_packages, 'pydub')
        pyaudioop_path = os.path.join(pydub_path, 'pyaudioop.py')
        
        if os.path.exists(pyaudioop_path):
            # Load pyaudioop module directly from file
            spec = importlib.util.spec_from_file_location("pyaudioop", pyaudioop_path)
            if spec and spec.loader:
                pyaudioop = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pyaudioop)
                
                # Register as both pyaudioop and audioop
                sys.modules['pyaudioop'] = pyaudioop
                sys.modules['audioop'] = pyaudioop
                break
except Exception:
    # If this fails, pydub will handle the error
    pass

