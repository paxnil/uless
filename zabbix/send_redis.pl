#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Std;

my %opts;
getopts('z:h:', \%opts);

chomp(my $pass = `grep ^requirepass /etc/redis/redis.conf | cut -d\\\" -f2`);
my @info = do { local $/="\r\n"; grep { chomp; } `/usr/bin/redis-cli -a $pass INFO`; };

open(SENDER, "| zabbix_sender -z $opts{z} -i -") or die "Failed to start zabbix_sender";

my ($scope, $k, $v, %sub, $i, @keyspaces, @slaves);
foreach (@info) {
  next if /^$/;
  if (/^# (\w+)/) {
    $scope = lc $1;
    next;
  }
  ($k, $v) = /^(\w+):(.+)$/;
  push @keyspaces, $k if ($scope eq 'keyspace' && $k =~ /^db\d+/);
  push @slaves, $k if ($scope eq 'replication' && $k =~ /^slave\d+/);
  if ($v =~ /[=,]/) {
    %sub = split /[=,]/, $v;
    foreach $i (keys %sub) {
      print SENDER "\"$opts{h}\" redis.${scope}[$k,$i] $sub{$i}\n";
    }
    next;
  }
  print SENDER "\"$opts{h}\" redis.${scope}[$k] $v\n";
}

print SENDER "\"$opts{h}\" redis.keyspaces ", '{"data":[{"{#DBN}":"', join('"},{"{#DBN}":"', @keyspaces), '"}]}', "\n";
print SENDER "\"$opts{h}\" redis.slaves ", '{"data":[{"{#SLN}":"', join('"},{"{#SLN}":"', @slaves), '"}]}', "\n" if @slaves > 0;
