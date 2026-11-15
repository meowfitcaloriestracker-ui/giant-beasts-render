import os, sys, runpy
sys.argv = ["fight.py", "sfx", os.environ.get("SFX_OUT", "sfx.wav")]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fight.py"), run_name="__main__")
