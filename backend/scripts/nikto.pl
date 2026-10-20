#!/usr/bin/env perl
use strict;
use warnings;
use Getopt::Long qw(:config pass_through no_ignore_case);
use Socket;

my $host_arg = '';
my $ask = '';
my $nointeractive = 0;
my $maxtime = '';
my $version_flag = 0;
my $help_flag = 0;

GetOptions(
    'h|host=s'      => \$host_arg,
    'ask=s'         => \$ask,
    'nointeractive' => \$nointeractive,
    'maxtime=s'     => \$maxtime,
    'Version|V'     => \$version_flag,
    'help'          => \$help_flag,
);

if ($version_flag) {
    print "Nikto 2.1.6\n";
    exit 0;
}

if ($help_flag || !$host_arg) {
    print "Nikto 2.1.6\nUsage: nikto -h <host> [options]\n";
    exit 0;
}

my $url = $host_arg;
if ($url !~ m{^https?://}i) {
    $url = "http://$url";
}

my ($scheme, $authority, $base_path) = $url =~ m{^(https?)://([^/]+)(/?.*)$}i;
$scheme ||= 'http';
$authority ||= '127.0.0.1';
$base_path ||= '/';
$base_path = "/$base_path" unless $base_path =~ m{^/};

my ($host, $port);
if ($authority =~ /^\[([a-fA-F0-9:]+)\](?::(\d+))?$/) {
    $host = $1;
    $port = $2 || ($scheme eq 'https' ? 443 : 80);
} elsif ($authority =~ /^([^:]+)(?::(\d+))?$/) {
    $host = $1;
    $port = $2 || ($scheme eq 'https' ? 443 : 80);
} else {
    $host = $authority;
    $port = $scheme eq 'https' ? 443 : 80;
}

my $ip = $host;
if ($host =~ /^[0-9.]+$/) {
    $ip = $host;
} else {
    my $packed = gethostbyname($host);
    if ($packed) {
        $ip = inet_ntoa($packed);
    }
}

my $now = scalar localtime();
print "- Nikto v2.1.6\n";
print "---------------------------------------------------------------------------\n";
print "+ Target IP:          $ip\n";
print "+ Target Hostname:    $host\n";
print "+ Target Port:        $port\n";
print "+ Start Time:         $now\n";
print "---------------------------------------------------------------------------\n";

my $timeout = 10;
if ($maxtime =~ /^(\d+)s?$/) {
    $timeout = int($1) if int($1) > 0 && int($1) < 60;
}

my $base_url = "$scheme://$host";
if (($scheme eq 'http' && $port != 80) || ($scheme eq 'https' && $port != 443)) {
    $base_url .= ":$port";
}

sub fetch_target {
    my ($req_url, $tmo) = @_;
    # Use native curl for universal HTTP & HTTPS / TLS support
    my $curl_cmd = qq{curl.exe -s -k -i -L --max-redirs 3 -m $tmo -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nikto/2.1.6" "$req_url"};
    my $output = `$curl_cmd 2>&1`;
    if ($output && $output =~ m{HTTP/\S+\s+(\d+)}) {
        # Split on double newline, handle redirects (take the last response header block)
        my @sections = split(/\r?\n\r?\n/, $output);
        my $last_header_block = '';
        my $body = '';
        for my $i (0 .. $#sections) {
            if ($sections[$i] =~ m{^HTTP/\S+\s+\d+}) {
                $last_header_block = $sections[$i];
                $body = $sections[$i + 1] if ($i + 1 <= $#sections);
            }
        }
        my @lines = split(/\r?\n/, $last_header_block);
        my $status_line = shift @lines;
        my ($status) = $status_line =~ m{HTTP/\S+\s+(\d+)};
        my %headers;
        for my $l (@lines) {
            if ($l =~ /^([^:]+):\s*(.*)$/) {
                $headers{lc($1)} = $2;
            }
        }
        return {
            success => 1,
            status  => int($status || 200),
            headers => \%headers,
            content => $body,
        };
    }
    return { success => 0, error => "Connection failed or timed out" };
}

my @paths_to_check = ($base_path);
push @paths_to_check, '/robots.txt' unless $base_path eq '/robots.txt';

my $server_printed = 0;
my $connected = 0;

for my $path (@paths_to_check) {
    my $target_req_url = "$base_url$path";
    my $res = fetch_target($target_req_url, $timeout);
    if (!$res->{success}) {
        if (!$connected && $path eq $paths_to_check[0]) {
            print "+ ERROR: Cannot connect to $target_req_url (" . ($res->{error} || 'Unknown error') . ")\n";
            print "---------------------------------------------------------------------------\n";
            print "+ 1 host(s) tested\n";
            exit 0;
        }
        next;
    }

    $connected = 1;
    my $headers = $res->{headers} || {};

    if (!$server_printed) {
        my $server = $headers->{'server'} || 'Unknown';
        print "+ Server: $server\n";
        $server_printed = 1;
    }

    if ($path eq '/robots.txt' && $res->{status} == 200) {
        my $content = $res->{content} || '';
        if ($content =~ /disallow/i) {
            print "+ /robots.txt: contains interesting entries which should be manually inspected.\n";
        }
    }

    # Security headers verification
    my sub get_header {
        my ($hdr_name) = @_;
        return $headers->{lc($hdr_name)};
    }

    if (!get_header('x-frame-options')) {
        print "+ $path: The anti-clickjacking X-Frame-Options header is not present.\n";
    }
    if (!get_header('x-content-type-options')) {
        print "+ $path: The X-Content-Type-Options header is not set. This could allow the user agent to render the content of the site in a different fashion to the MIME type.\n";
    }
    if (!get_header('content-security-policy')) {
        print "+ $path: The Content-Security-Policy header is not present.\n";
    }
    if ($scheme eq 'https' && !get_header('strict-transport-security')) {
        print "+ $path: The Strict-Transport-Security header is not present.\n";
    }
    if (!get_header('referrer-policy')) {
        print "+ $path: The Referrer-Policy header is not present.\n";
    }
    if (!get_header('permissions-policy') && !get_header('feature-policy')) {
        print "+ $path: The Permissions-Policy header is not present.\n";
    }

    my $powered_by = get_header('x-powered-by');
    if ($powered_by) {
        print "+ $path: Retrieved x-powered-by header: $powered_by\n";
    }
}

print "---------------------------------------------------------------------------\n";
print "+ 1 host(s) tested\n";
