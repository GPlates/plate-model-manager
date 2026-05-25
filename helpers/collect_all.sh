#!/bin/bash

# ./collect_all.sh ./model-repo

set -euo pipefail

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <model-repo-dir>"
	exit 1
fi

target_dir="$1"

python3 collect_alfonso2024.py "$target_dir"
python3 collect_cao2020.py "$target_dir"
python3 collect_cao2024.py "$target_dir"
python3 collect_clennett2020_m2019.py "$target_dir"
python3 collect_clennett2020_s2013.py "$target_dir"
python3 collect_domeier2014.py "$target_dir"
python3 collect_gibbons2015.py "$target_dir"
python3 collect_golonka.py "$target_dir"
python3 collect_gurnis2012.py "$target_dir"
python3 collect_matthews2016_mantle_ref.py "$target_dir"
python3 collect_matthews2016_pmag_ref.py "$target_dir"
python3 collect_merdith2021.py "$target_dir"
python3 collect_muller2008.py "$target_dir"
python3 collect_muller2016.py "$target_dir"
python3 collect_muller2019.py "$target_dir"
python3 collect_muller2022.py "$target_dir"
python3 collect_paleomap.py "$target_dir"
python3 collect_pehrsson2015.py "$target_dir"
python3 collect_rodinia.py "$target_dir"
python3 collect_scotese_and_wright2018.py "$target_dir"
python3 collect_seton2012.py "$target_dir"
python3 collect_shephard2013.py "$target_dir"
python3 collect_shirmard2025.py "$target_dir"
python3 collect_torsvikcocks2017.py "$target_dir"
python3 collect_young2018.py "$target_dir"
python3 collect_zahirovic2014.py "$target_dir"
python3 collect_zahirovic2016.py "$target_dir"
python3 collect_zahirovic2022.py "$target_dir"