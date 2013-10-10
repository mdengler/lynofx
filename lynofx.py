#!/usr/bin/env python

# Copyright 2005-2010 Wesabe, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# lynofx.py - Issue OFX requests from the command line
# 

import getpass
import optparse
import os
import os.path
import sys
import urllib2

sys.path.insert(0, 'fixofx/3rdparty')
sys.path.insert(0, 'fixofx/lib')

import ofx

VERSION = "%prog 1.0"

actions = ["profile", "accounts", "statement"]

__doc__ = \
"""Command-line client for making OFX requests and showing the responses that
come back. Use option flags to pass the OFX client parameters for the request,
and then specify the request type as the action. Each financial institution
has a set of parameters that are needed to make requests; those parameters are
not provided by this script but must be found elsewhere (for instance, see
http://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings). By default, the
response will be shown as a pretty-printed OFX/2.0 document, but the raw
response will be shown instead if the -r/--raw option is passed.

Possible actions are: 
`profile` - get a profile of this OFX server's capabilities. 
`accounts` - get a list of accounts for an authenticated user. 
`statement` - get a single account statement for an authenticated user.
"""

parser = optparse.OptionParser(usage="%prog [options] (profile|accounts|statement)", 
                               version=VERSION, description=__doc__)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=False, help="be more talkative, social, outgoing")
parser.add_option("-r", "--raw", action="store_true", dest="raw",
                  default=False, help="show raw response (don't pretty-print as OFX/2.0)")
parser.add_option("-f", "--fid", dest="fid",
                  help="OFX ID of the financial institution")
parser.add_option("-o", "--org", dest="org", 
                  help="OFX organization of the financial institution")
parser.add_option("-u", "--url", dest="url", 
                  help="OFX URL of the financial institution")
parser.add_option("-t", "--accttype", dest="accttype", 
                  help="type of the account")
parser.add_option("-i", "--acctid", dest="acctid", 
                  help="ID of the account (a.k.a. account number)")
parser.add_option("-b", "--bankid", dest="bankid", 
                  help="ID of the bank (a.k.a. routing number)")
parser.add_option("-U", "--username", "--user", dest="username", 
                  help="username to log in as")
parser.add_option("-P", "--password", dest="password", 
                  help="password to use for login")
(options, args) = parser.parse_args()

if len(args) != 1:
    sys.stderr.write("Call lynofx.py with one and only one action (use --help for more info).\n")
    sys.exit(1)

action = args[0]  # just for clarity

if action not in actions:
    sys.stderr.write("Unrecognized option '%s' (use --help for more info).\n" % action)
    sys.exit(1)

if options.verbose:
    sys.stderr.write("Using options:\n")
    sys.stderr.write("  action:   %s\n" % action)
    if options.fid:      sys.stderr.write("  fid:      %s\n" % options.fid)
    if options.org:      sys.stderr.write("  org:      %s\n" % options.org)
    if options.url:      sys.stderr.write("  url:      %s\n" % options.url)
    if options.accttype: sys.stderr.write("  accttype: %s\n" % options.accttype)
    if options.acctid:   sys.stderr.write("  acctid:   %s\n" % options.acctid)
    if options.bankid:   sys.stderr.write("  bankid:   %s\n" % options.bankid)
    if options.username: sys.stderr.write("  username: %s\n" % options.username)
    if options.password: sys.stderr.write("  password: %s\n" % ("<hidden>" if options.username else "<unset>"))
    sys.stderr.write("\n")

# FIXME: should check to make sure all required options for this action were provided.

if action != "profile":
    # The following allows the username prompt to be written even if output is redirected.
    # On UNIX and Mac, that is. The sys.stdout fallback should work elsewhere, assuming
    # people on those other platforms aren't redirecting output like the UNIX-heads are.
    terminal = None
    if os.access("/dev/tty", os.W_OK):
        terminal = open("/dev/tty", 'w')
    else:
        terminal = sys.stdout
    if not options.username:
        terminal.write("Enter account username: ")
        options.username = sys.stdin.readline().rstrip()
    if not options.password:
        options.password = getpass.getpass("Enter account password: ")

institution = ofx.Institution(ofx_org=options.org, 
                              ofx_url=options.url, 
                              ofx_fid=options.fid)

account     = ofx.Account(acct_type=options.accttype, 
                          acct_number=options.acctid, 
                          aba_number=options.bankid, 
                          institution=institution)

try:
    client   = ofx.Client(debug=options.verbose)
    response = None

    if options.verbose:
        # Install an HTTP handler with debug output
        http_handler  = urllib2.HTTPHandler(debuglevel=1)
        https_handler = urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(http_handler, https_handler)
        urllib2.install_opener(opener)
        
        sys.stderr.write("HTTP Debug Output:\n")
        sys.stderr.write("==================\n")
        sys.stderr.write("\n")
    
    if action == "profile":
        response = client.get_fi_profile(institution)

    elif action == "accounts":
        response = client.get_account_info(institution, options.username, options.password)

    elif action == "statement":
        response = client.get_statement(account, options.username, options.password)
    
    if options.verbose:
        sys.stderr.write("\n")
        sys.stderr.write("Request Message:\n")
        sys.stderr.write("================\n")
        sys.stderr.write("\n")
        sys.stderr.write(client.get_request_message())
        sys.stderr.write("\n")
        sys.stderr.write("Response Message:\n")
        sys.stderr.write("=================\n")
        sys.stderr.write("\n")
    
    if options.raw:
        sys.stdout.write(response.as_string() + "\n")
    else:
        sys.stdout.write(response.as_xml() + "\n")

except ofx.Error, exception:
    if options.verbose:
        sys.stderr.write("\n")
        sys.stderr.write("Request Message:\n")
        sys.stderr.write("================\n")
        sys.stderr.write("\n")
        sys.stderr.write(client.get_request_message() + "\n")
        sys.stderr.write("\n")
    
    sys.stderr.write("*** Server returned an OFX error:\n")
    sys.stderr.write(str(exception))
    sys.stderr.write("\n")
    sys.exit(3)

except urllib2.HTTPError, exception:
    if options.verbose:
        sys.stderr.write("\n")
        sys.stderr.write("Request Message:\n")
        sys.stderr.write("================\n")
        sys.stderr.write("\n")
        sys.stderr.write(client.get_request_message() + "\n")
        sys.stderr.write("\n")
    
    sys.stderr.write("*** Server returned an HTTP error:\n")
    sys.stderr.write(str(exception))
    sys.stderr.write(str(exception.hdrs))
    sys.stderr.write(exception.fp.read())
    sys.stderr.write("\n")
    sys.exit(4)
    
