An exploration of a potential replacement for curc-bench


## Goals

- be able to run arbitrary tests without modifications
- be able to support collection of metrics
- be able to run tests outside of general testing reservations


## Examples

```
sbench.py --state IDLE --state MIXED --account admin --time=0:10:00 --bcast=/tmp/check_check.py --chdir /tmp -- $(readlink -f checks/check_check.py)
```

### Checks

The checks can, of course, be run directly. Each has a `--help`.

```
check_check.py
```

```
check_intel_linpack.py -- /curc/sw/intel/17.4/compilers_and_libraries_2017.4.196/linux/mkl/benchmarks/linpack/xlinpack_xeon64
```

```
check_stream.py -- env LD_LIBRARY_PATH=/curc/sw/intel/17.4/compilers_and_libraries_2017.4.196/linux/compiler/lib/intel64:/curc/sw/gcc/5.4.0/lib64 /projects/rcops/CurcBenchBenchmarks/stream/stream.o
```


## References

https://github.com/ResearchComputing/curc-bench/blob/master/src/bench/conf/node_conf.py
