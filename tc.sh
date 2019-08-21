

sudo  tc qdisc  add dev enp2s0 root netem loss 1%
sudo  tc qdisc  change dev enp2s0 root netem loss 1%
sudo  tc qdisc  del dev enp2s0 root netem loss 1%


