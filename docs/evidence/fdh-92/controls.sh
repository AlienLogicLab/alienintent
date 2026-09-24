#!/usr/bin/env bash
# FDH-92 criterion 5: discriminating proof. Run from the repository root of a candidate checkout.
# Builds three scratch trees outside the checkout, runs the new tests against each, and writes one
# log per run (ending in its exit status) into docs/evidence/fdh-92/. The checkout is not modified
# apart from those logs and variants.diff.
set -u
BASELINE=${BASELINE:-0eda915}
EV=docs/evidence/fdh-92
T=tools/orchestration
W=$(mktemp -d /tmp/fdh92-controls.XXXXXX)
trap 'rm -rf "$W"' EXIT

AC12=("$T/test_factory_director_inputs.py::test_wip_intentionally_full"
      "$T/test_factory_director_inputs.py::test_overlap_with_only_worker_work_pending_idles_wip_intentionally_full"
      "$T/test_factory_director_inputs.py::test_overlap_with_no_control_required_idles_wip_intentionally_full"
      "$T/test_factory_director_host.py::test_claims_above_the_wip_limit_idle_as_wip_intentionally_full")
AC6=("$T/test_factory_director_docs.py::test_documented_wip_predicates_are_the_ones_the_adapter_derives")
AC3=("$T/test_factory_director_inputs.py::test_overlap_never_suppresses_director_only_control"
     "$T/test_factory_director_host.py::test_claims_above_the_wip_limit_never_suppress_director_only_control")

# Baseline: the code at $BASELINE with the candidate's two test files.
mkdir -p "$W/baseline"
git archive "$BASELINE" tools docs/operations config | tar -x -C "$W/baseline"
cp "$T/test_factory_director_inputs.py" "$T/test_factory_director_host.py" "$W/baseline/$T/"
# "==" variant and suppressing variant: the candidate tree with exactly one line changed.
for variant in eq suppress; do
  mkdir -p "$W/$variant"
  tar -c tools docs/operations config | tar -x -C "$W/$variant"
done
sed -i 's/wip_intentionally_full=runtime.claims >= wip_limit,/wip_intentionally_full=runtime.claims == wip_limit,/' \
  "$W/eq/$T/factory_director_inputs.py"
sed -i 's/        if values.wip_intentionally_full and not values.director_only_control():/        if values.wip_intentionally_full:/' \
  "$W/suppress/$T/factory_director_host.py"
(cd "$W" && diff -u "suppress/$T/factory_director_inputs.py" "eq/$T/factory_director_inputs.py"
            diff -u "eq/$T/factory_director_host.py" "suppress/$T/factory_director_host.py") > "$EV/variants.diff"

run() {
  local name=$1 dir=$2; shift 2
  (cd "$dir" && python3 -m pytest -q -p no:cacheprovider -rfE "$@") > "$EV/$name.log" 2>&1
  echo "exit=$?" >> "$EV/$name.log"
  echo "$name: $(tail -n 2 "$EV/$name.log" | tr '\n' ' ')"
}
run 1-baseline-ac1-2 "$W/baseline" "${AC12[@]}"              # expected: fail
run 2-baseline-ac3 "$W/baseline" "${AC3[@]}"                 # expected: pass (regression guards)
run 3-eq-variant-ac1-2 "$W/eq" "${AC12[@]}"                  # expected: fail
run 3b-eq-variant-ac6 "$W/eq" "${AC6[@]}"                    # expected: fail (contract and code disagree)
run 4-suppress-variant-ac3 "$W/suppress" "${AC3[@]}"         # expected: fail
run 5-candidate-ac1-3-6 . "${AC12[@]}" "${AC3[@]}" "${AC6[@]}" # expected: pass
run 6-candidate-fdh-suites . "$T/test_factory_director_inputs.py" "$T/test_factory_director_host.py" \
  "$T/test_factory_director_docs.py"                         # expected: pass
