#!/bin/bash
# Create PID directory for Elastic Beanstalk
mkdir -p /var/pids
chown webapp:webapp /var/pids
