#!/usr/bin/python3
#
# Project: py-nugetfee
# File: main.py
#
# Copyright 2015 Matthew Mitchell
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib.parse
import coinrpc
import configparser
import sys
import os

HTTP_OK = "200 OK"
HTTP_METHOD_NOT_ALLOWED = "405 Method Not Allowed"
HTTP_UNSUPPORTED = "415 Unsupported media type"
HTTP_NOT_ACCEPTABLE = "406 Not Acceptable"
HTTP_NOT_FOUND = "404 Not Found"
HTTP_BAD_REQUEST = "400 Bad Request"
HTTP_INTERNAL_SERVER_ERROR = "500 Internal Server Error"

COIN_METHOD_NOT_FOUND = -32601

GET_RESP = (
    b"Provide this URL with application/x-www-form-urlencoded POST data containing: \n" 
    b" - bytes: The number of bytes of the NuBits transaction.\n"
    b" - amount: The total output amount of the transaction. Formatted as a coin decimal (4 decimal places).\n"
    b"\n"
    b"The server will respond with the coin amount of the required NuBits fee."
)

TEXT_PLAIN_HEADERS = [('Content-Type', 'text/plain')]

REQ_MIME = "application/x-www-form-urlencoded"
RESP_MIME = "text/plain"

def is_acceptable(header, expect):

    start = expect.split("/")[0]

    for mime in header.split(","):
        mime = mime.strip()
        if mime in ["*/*", start + "/*", expect]:
            return True

    return False

class Application():

    def __init__(self, conf_file=None):

        if conf_file is None:
            conf_file = "~/.nu/nu.conf"

        conf_file = os.path.expanduser(conf_file)

        if not os.path.exists(conf_file):
            sys.exit("Nu conf does not exist")

        parser = configparser.ConfigParser({
            "rpchost" : "localhost",
            "rpcport" : 14002
        })

        parser.read_string(
            "[dummy]\n" + open(conf_file).read()
        )

        conf = parser["dummy"];

        self.rpc = coinrpc.CoinRpc(
            conf["rpcuser"],
            conf["rpcpassword"],
            conf["rpchost"],
            int(conf["rpcport"]) + 1,
            4
        )

    def __call__(self, env, start_response):

        if env['REQUEST_METHOD'] != "POST":

            allow_headers = [("Allow", "POST, GET")]

            if env['REQUEST_METHOD'] == "OPTIONS":
                # Preflight requests need to be implemented for Ajax queries
                allow_headers.append(('Access-Control-Allow-Headers', 'Content-Type, Accept, Accept-Encoding, Content-Length, Host, Origin, User-Agent, Referer'))
                start_response(HTTP_OK, allow_headers)
                return [b""]
            elif env['REQUEST_METHOD'] == "GET":
                start_response(HTTP_OK, TEXT_PLAIN_HEADERS)
                return [GET_RESP]
            else:
                start_response(HTTP_METHOD_NOT_ALLOWED, allow_headers)
                return [b""]

        # If content type is set, should be application/x-www-form-urlencoded
        if "CONTENT_TYPE" in env and env["CONTENT_TYPE"] != REQ_MIME:
            start_response(HTTP_UNSUPPORTED, [])
            return [b""]

        # If accept header is set, should be application/octet-stream
        if 'HTTP_ACCEPT' in env and not is_acceptable(env['HTTP_ACCEPT'], RESP_MIME):
            start_response(HTTP_NOT_ACCEPTABLE, [])
            return [b""]

        try:

            post_data = urllib.parse.parse_qs(env['wsgi.input'].read(), strict_parsing=True)
            if b"bytes" not in post_data or b"amount" not in post_data:
                raise ValueError
            
            byte_size = int(post_data[b"bytes"][0])
            amount = float(post_data[b"amount"][0])
            
        except ValueError:
            start_response(HTTP_BAD_REQUEST, [])
            return [b""]

        # Try getfee command first

        try:
            fee = self.rpc.call("getfee", byte_size, amount)
        except coinrpc.JSONRPCException as e:

            try:
                if e.args[0]["code"] == COIN_METHOD_NOT_FOUND:
                    # Fallback to getinfo
                    fee = self.rpc.call("getinfo")["paytxfee"] * (1 + byte_size // 1000)
                else:
                    raise 

            except coinrpc.JSONRPCException as e:
                start_response(HTTP_INTERNAL_SERVER_ERROR, [])
                return [bytes(e.args[0]["message"])]

        start_response(HTTP_OK, [('Content-Type', RESP_MIME)])
        return [bytes(str(fee), 'utf-8')]
        
