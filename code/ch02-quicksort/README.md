# Chapter 2 Lab: Quicksort Performance Analysis

This directory contains the starter code for the Chapter 2 lab.

## What is here

```text
code/ch02-quicksort/
├── Makefile
├── README.md
├── main.c
├── src/
│   └── quicksort.c
├── datasets/
└── outputs/
```

The program reads integers from a text file, sorts them, and writes the
sorted result to `outputs/`.

## Quick start

```bash
make clean
make
make datasets N=100000
./qs datasets/random_100000.txt
```

## Useful targets

```bash
make datasets N=100000   # generate input files
make test N=100000       # run the four default patterns
make perf-all N=100000   # run perf across the four patterns
```

## Measurement workflow

Use the lab handout in
`src/part1-foundations/ch02-measurement-methodology/lab-quicksort-perf.md`
as the source of truth for the experiment design. At minimum, you should:

1. write a prediction before measuring;
2. collect multiple runs for each dataset;
3. save the raw `perf` or Valgrind output;
4. explain the result with evidence rather than with a guessed story.

## VM note

If PMU counters are unavailable in your VM, switch to Valgrind:

```bash
valgrind --tool=cachegrind --cache-sim=yes --branch-sim=yes \
  --cachegrind-out-file=outputs/random.cg.out \
  ./qs datasets/random_100000.txt
```

## Troubleshooting

- If `perf` requires privilege, use `sudo perf stat ...`.
- If Valgrind says `Permission denied`, send output to a fresh path inside
  `outputs/`.
- If a dataset is missing, regenerate it with `make datasets N=<size>`.
