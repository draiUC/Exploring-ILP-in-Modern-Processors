"""Install only this task's four new files into gem5 and build incrementally."""
from pathlib import Path
import shutil
import subprocess

here=Path(__file__).resolve().parent
repo=Path.home()/'src/gem5'
target=repo/'src/cpu/five_stage'
if not (repo/'SConstruct').is_file():raise RuntimeError('gem5 source missing')
target.mkdir(exist_ok=True)
for name in ['SConscript','FiveStageCPU.py','five_stage_cpu.hh','five_stage_cpu.cc']:
    shutil.copy2(here/name,target/name)
subprocess.run(['scons','build/ARM/gem5.opt','-j8','CC=gcc-13','CXX=g++-13'],cwd=repo,check=True)
