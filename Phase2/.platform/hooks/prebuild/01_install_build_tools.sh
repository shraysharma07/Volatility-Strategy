#!/bin/bash
yum update -y
yum groupinstall "Development Tools" -y
yum install gcc-c++ -y
yum install mesa-libGL-devel -y
