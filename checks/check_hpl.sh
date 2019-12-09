#!/bin/bash
#SBATCH --job-name=linpack
#SBATCH --nodes=1
#SBATCH --exclusive
#SBATCH --time=0:45:00

LINPACK=/curc/sw/intel/17.4/compilers_and_libraries_2017.4.196/linux/mkl/benchmarks/linpack/xlinpack_xeon64

function main
{
    $LINPACK "$@"
}


main "$@"
