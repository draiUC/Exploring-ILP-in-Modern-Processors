Assignment 4 - Exploring Instruction-Level Parallelism (ILP) in Modern Processors

The codebase, configuration files, screenshots, charts, and measured results
are in the folders below.

code/                           gem5 configs, six ARM assembly workloads,
                                Hello World source, runners, analysis and plots
code/five_stage/                C++ five-stage teaching CPU, config and runner
results/                        Cases: each config.ini, stats.txt,
                                and exit.json; summary files and representative
                                O3 trace/viewer output; Hello World and issue log
results_five_stage/             Prediction on/off runs: configs, stats,
                                pipeline traces, state checks; negative control
figures/                        Charts drawn from measured results
screenshots/                    Captures of saved configuration, output,
                                pipeline, comparison and troubleshooting files

Gem5 runs use the pinned gem5 recorded in
results/manifest.json. The 14 five-stage runs use the same CPU class with
prediction enabled or disabled, and are documented in code/five_stage/README.txt.
The model has an intentionally small teaching ISA, separate from AArch64.

Start PowerShell and run:
  wsl -d gem5-Ubuntu-24.04

The installed simulator is ~/src/gem5/build/ARM/gem5.opt. To rerun the original
workloads after copying this package to ~/assignment4/ in WSL:
  cd ~/assignment4/code
  python3 run_experiments.py
  python3 analyze.py
  python3 plot_results.py

The runner compiles the .S files using gcc-13 and creates the full traces.
The archive retains one representative O3 trace, results/integer_w1/trace.out,
so the official viewer can also be rerun without repeating all experiments:
  cd ~/assignment4
  python3 ~/src/gem5/util/o3-pipeview.py --only_committed --timestamps \
    -c 1000 -i 400:430 -o pipeline-view.txt results/integer_w1/trace.out

To rebuild and run Hello World using the included source:
  cd ~/assignment4
  gcc-13 -static -O2 -o code/hello/hello-arm64 code/hello/hello.c
  ~/src/gem5/build/ARM/gem5.opt --outdir=hello-output code/hello/arm-smoke.py

To rerun the five-stage comparisons:
  cd ~/assignment4/code/five_stage
  python3 run_five_stage.py
  python3 plot_five_stage.py
