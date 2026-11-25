#!/bin/sh
# Rebuilds the rev A board from scratch. Needs KiCad's Python (pcbnew) and kicad-cli on the path.
set -e
cd "$(dirname "$0")"
python3 gen_board.py
python3 place_parts.py
python3 make_project.py
printf '(fp_lib_table\n  (lib (name "gg_card")(type "KiCad")(uri "${KIPRJMOD}/gg_card.pretty")(options "")(descr "Hybrid card: custom footprints"))\n)\n' > out/fp-lib-table
rm -rf out/gg_card.pretty && cp -r gg_card.pretty out/
python3 render.py
python3 make_assembly.py
python3 make_step.py
