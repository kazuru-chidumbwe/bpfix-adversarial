# Vagrant — Debian 13 userspace for SoftwareX lab helpers
#
# This provisions a Debian 13 (trixie) x86_64 VM with clang/bpftool/python.
# It does NOT guarantee SoftwareX cite kernel 6.12.86+deb13-amd64 — that comes
# from Debian's linux-image package after install/reboot. Always record
# `uname -r` into results/env_pins/ before treating captures as SoftwareX-cite.
#
# Usage:
#   vagrant up
#   vagrant ssh
#   # follow docs/LAB-PIN.md inside the guest

Vagrant.configure("2") do |config|
  config.vm.box = "debian/trixie64"
  config.vm.hostname = "bpfix-lab"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 4096
    vb.cpus = 2
  end
  config.vm.provision "shell", inline: <<-SHELL
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y build-essential clang llvm libbpf-dev bpftool \
      python3 python3-venv python3-pip git make linux-headers-$(uname -r) || true
    echo "=== SoftwareX lab pin check ==="
    uname -a
    clang --version | head -n1 || true
    bpftool version || true
    echo "If uname -r != 6.12.86+deb13-amd64, install matching linux-image and reboot."
    echo "See docs/LAB-PIN.md"
  SHELL
end
