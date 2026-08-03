#!/usr/bin/env bash
# Mirror every primary source this project cites into ./sources/.
#
# WHY THIS EXISTS
#
# Until now the only source held locally was the KJV (committed, in
# luckylutheran/data/) and the Common Service Book page scans (csb_jp2.zip,
# gitignored). Everything else — the Triglotta behind all 49 catechism
# portions, the ELHB behind most of Matins and Vespers, the Rule of St
# Benedict behind the night psalms — existed only as an archive.org
# identifier in a table in SOURCES.md.
#
# That is fine until it isn't. Items get taken down, re-identified, or moved
# behind lending. When that happens the derived YAML in this repo is still
# correct but nobody can *re-verify* it, and "everything is cited" quietly
# becomes "everything was cited once, by someone, who is no longer here". The
# whole project rests on being able to check the claim again later.
#
# So: pull the text layers locally, and prove each one is the right book by
# grepping for a phrase we actually quote from it. A silent 404 that writes an
# HTML error page to disk is the failure this guards against — it happened
# during the Benedict search and cost a round trip.
#
# The files are gitignored (see *_djvu.txt and sources/ in .gitignore): large,
# re-fetchable, and not ours to redistribute. Only our *derived* citation data
# belongs in the repo.
#
# Page images are a separate matter and are NOT fetched here — only the CSB's
# are needed, they are 387MB, and docs/lectionary-migration/README.md carries
# those commands.
#
# Usage:  bash tools/fetch_sources.sh          # fetch what is missing
#         bash tools/fetch_sources.sh --force  # re-fetch everything

set -uo pipefail
cd "$(dirname "$0")/.."
DEST=sources
mkdir -p "$DEST"
FORCE=${1:-}

# identifier | what it is | a phrase this project quotes from it
ITEMS=(
"concordiatriglot00unse|Concordia Triglotta (CPH, 1921) — English column; every catechism portion and Luther's Morning/Evening Prayers|What does this mean"
"commonserviceboo00phil|Common Service Book of the Lutheran Church (1917) — Matins, Vespers, Evening Suffrages, collects, lectionary, psalm table|The Evening Suffrages may be said"
"evangelicalluthe09evan|Evangelical Lutheran Hymn-Book (CPH, 1909) — the ELHB liturgy cited for Matins/Vespers. The 1912 printing was used via Project Wittenberg, which records no locator; these archive.org editions are the citable substitute|But Thou, O Lord, have mercy upon us"
"evangelicallu93evan|Evangelical Lutheran Hymn-Book (1893) — earlier ELHB printing, for collation|But Thou, O Lord, have mercy upon us"
"churchliturgyfor00evan|Church Liturgy ... Evangelical Lutheran Synod of Missouri (CPH, 1881) — the Confession in the retired Compline order|poor sinful being"
"TheRuleOfStBenedict|The Rule of St Benedict (1907), English with the Latin alongside — ch. 18, the night psalms|Ad Completorium"
"TheRuleOfOurMostHolyFather|The Rule of our most Holy Father St Benedict (1875) — second witness to ch. 18|hundred-and-thirty-third"
"rulestbenedictf00benegoog|The Rule of St Benedict, from the English edition of 1638 (1875) — third witness to ch. 18|hundred-and-thirty-third"
"bookofcommonpray00chur_20|BCP with the Additions and Deviations Proposed in 1928 (CC0) — source of the RETIRED Compline order. Kept so the retired file stays checkable; nothing live cites it|snares of the enemy"
)

ok=0; bad=0
for row in "${ITEMS[@]}"; do
  IFS='|' read -r id desc probe <<<"$row"
  out="$DEST/${id}_djvu.txt"

  if [[ -s "$out" && "$FORCE" != "--force" ]]; then
    printf '  = %-32s (have it)\n' "$id"; ok=$((ok+1)); continue
  fi

  curl -sL --max-time 300 "https://archive.org/download/${id}/${id}_djvu.txt" -o "$out"

  # archive.org answers a missing item with an HTML error page, HTTP 200.
  if head -c 200 "$out" | grep -qi '<!DOCTYPE html\|<html'; then
    printf '  ! %-32s FETCH FAILED (got an HTML error page)\n' "$id"
    rm -f "$out"; bad=$((bad+1)); continue
  fi

  # Prove it is the right book. The scans double-space words and wrap
  # mid-phrase, so flatten whitespace before matching or this false-negatives.
  # Keep probes SHORT and free of hyphens: flattening joins the lines but
  # leaves the hyphen, so "repe- tantur" never matches "repetantur".
  if tr -s ' \t\n' ' ' < "$out" | grep -qi -- "$probe"; then
    printf '  + %-32s %s\n' "$id" "$(du -h "$out" | cut -f1)"; ok=$((ok+1))
  else
    printf '  ! %-32s WRONG BOOK? probe not found: %s\n' "$id" "$probe"
    bad=$((bad+1))
  fi
done

echo
echo "$ok ok, $bad failed  ->  $DEST/"
echo "Grep these flattened, per docs/lectionary-migration/README.md:"
echo "  tr -s ' \\t\\n' ' ' < $DEST/<id>_djvu.txt | grep -o -i -E '.{200}PHRASE.{200}'"
[[ $bad -eq 0 ]]
