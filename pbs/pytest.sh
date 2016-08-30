#!/bin/bash
for i in $(ls test/*.py);do PYTHONPATH=. python $i; done
