#!/bin/sh
# copy a staged case (series + binout) from uploads into the analysis workspace
U="<PROJECT_ROOT>/15_LS_DYNA_Extension/12C_Nonlinear_Buckling"
for c in "$@"; do
  cp "$U/results/series/${c}_series.csv" "$U/results/series/${c}_summary.json" series/
  mkdir -p binout/$c && cp "$U/runs/$c/binout" binout/$c/
done
