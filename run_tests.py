#!/usr/bin/env bash
# This requires nose and coverage.
nosetests test pybeanstream --nologcapture -s --with-coverage --cover-package=pybeanstream
