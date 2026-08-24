# {{cookiecutter.plugin_name}} — Daisy Seed firmware.
#
# Set LIBDAISY_DIR to point at your actual libDaisy checkout, either here or via
# `make LIBDAISY_DIR=/path/to/libDaisy`. See README.md -- this is an unverified
# starting stub, not a confirmed-working build.

LIBDAISY_DIR ?= ../../libDaisy

TARGET = {{cookiecutter.plugin_name_lowercase}}_daisy
CPP_SOURCES = main.cpp

SYSTEM_FILES_DIR = $(LIBDAISY_DIR)/core
include $(SYSTEM_FILES_DIR)/Makefile
