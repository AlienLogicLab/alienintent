#!/usr/bin/env bash
# FDH-91 criterion 5: discriminating proof. Run from the repository root of a candidate checkout.
# Builds scratch trees outside the checkout (each baseline's code with the candidate's two test
# files, and the candidate with only the adapter preflight call disabled), runs the new tests
# against each, and writes one log per run (ending in its exit status) into docs/evidence/fdh-91/.
# The checkout is not modified apart from those logs.
set -u
EV=docs/evidence/fdh-91/verifier-jc
T=tools/orchestration
W=$(mktemp -d /tmp/fdh91-controls.XXXXXX)
trap 'rm -rf "$W"' EXIT

AC1=("$T/test_factory_director_docs.py::test_env_file_guidance_requires_a_path_that_resolves_every_host_tool")
AC2_SEED=("$T/test_factory_director_docs.py::test_installer_seeds_a_new_env_file_with_commented_path_guidance")
AC2_KEEP=("$T/test_factory_director_docs.py::test_installer_leaves_an_existing_env_file_byte_identical")
AC3=("$T/test_factory_director_inputs.py::test_unresolvable_gh_fails_closed_naming_gh_and_the_searched_path"
     "$T/test_factory_director_inputs.py::test_host_records_the_unresolvable_gh_failure_with_the_refusal")
AC4=("$T/test_factory_director_inputs.py::test_resolvable_gh_leaves_adapter_behaviour_unchanged")

for baseline in 0eda915 669e5f1; do
  mkdir -p "$W/$baseline"
  git archive "$baseline" tools docs/operations config | tar -x -C "$W/$baseline"
  cp "$T/test_factory_director_inputs.py" "$T/test_factory_director_docs.py" "$W/$baseline/$T/"
done
# No-preflight variant: the candidate tree with the one require_gh() call replaced by pass.
mkdir -p "$W/nopreflight"
tar -c tools docs/operations config | tar -x -C "$W/nopreflight"
sed -i 's/            require_gh()  # the default readers run gh; injected readers do not/            pass/' \
  "$W/nopreflight/$T/factory_director_inputs.py"
(cd "$W" && diff -u "669e5f1/$T/factory_director_inputs.py" "nopreflight/$T/factory_director_inputs.py") \
  > "$EV/nopreflight-vs-669e5f1.diff"

run() {
  local name=$1 dir=$2; shift 2
  (cd "$dir" && python3 -m pytest -q -p no:cacheprovider -rfE "$@") > "$EV/$name.txt" 2>&1
  echo "exit=$?" >> "$EV/$name.txt"
  echo "$name: $(tail -n 2 "$EV/$name.txt" | tr '\n' ' ')"
}
for baseline in 0eda915 669e5f1; do
  run "1-$baseline-ac1-docs" "$W/$baseline" "${AC1[@]}"          # expected: fail
  run "2-$baseline-ac2-seed" "$W/$baseline" "${AC2_SEED[@]}"     # expected: fail
  run "3-$baseline-ac3-gh" "$W/$baseline" "${AC3[@]}"            # expected: fail
  run "4-$baseline-guards" "$W/$baseline" "${AC2_KEEP[@]}" "${AC4[@]}"  # expected: pass (regression guards)
done
run 5-nopreflight-ac3 "$W/nopreflight" "${AC3[@]}"               # expected: fail
run 6-candidate-ac1-4 . "${AC1[@]}" "${AC2_SEED[@]}" "${AC2_KEEP[@]}" "${AC3[@]}" "${AC4[@]}"  # expected: pass
run 7-candidate-fdh-suites . "$T/test_factory_director_inputs.py" "$T/test_factory_director_host.py" \
  "$T/test_factory_director_docs.py"                             # expected: pass
