#!/bin/bash

V4=reserved.v4
V6=reserved.v6

TAIL='"R0","Reserved addresses"'

bin2dec () {
  echo "ibase=2; $1" | bc
}

hex2dec () {
  echo "ibase=16; $(echo $1 | tr abcdef ABCDEF)" | bc
}

compress6 () {
  sipcalc -6 "$1" | grep 'Compressed address' | cut -d' ' -f3
}

while read net; do
  IFS='-' read fs ts <<< $(sipcalc $net | grep 'Network range' | tr -d ' \t' | cut -d- -f2-)
  read f t <<< $(sipcalc -b $net | sed -n '/Network range/,+1p' | expand | cut -c27-61 | tr -d .)
  echo -e "\"$fs\",\"$ts\",\"$(bin2dec $f)\",\"$(bin2dec $t)\",$TAIL"
done < $V4

while read net; do
  read fs ts <<< $(sipcalc -b $net | sed -n '/Network range/,+1p' | expand | cut -c27-66)
  f=$(echo $fs | tr -d :)
  t=$(echo $ts | tr -d :)
  echo -e "\"$(compress6 $fs)\",\"$(compress6 $ts)\",\"$(hex2dec $f)\",\"$(hex2dec $t),$TAIL"
done < $V6
