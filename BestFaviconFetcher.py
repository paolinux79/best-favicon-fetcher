
import os.path
import shutil

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Some hosts don't like the requests default UA. Use this one instead.
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 \
        Safari/537.36'
}


def parse_url(url):
    parsed_site_uri = urlparse(url)

    # Help the user out if they didn't give us a protocol
    if not parsed_site_uri.scheme:
        url = 'http://' + url
        parsed_site_uri = urlparse(url)

    if not parsed_site_uri.scheme or not parsed_site_uri.netloc:
        raise Exception("Unable to parse URL, %s" % url)

    return parsed_site_uri


def find_best_favicon_url(source, url):
    """
    https://stackoverflow.com/questions/21991044/how-to-get-high-resolution-website-logo-favicon-for-a-given-url
    Do-it-yourself algorithm

Look for Apple touch icon declarations in the code, such as <link rel="apple-touch-icon" href="/apple-touch-icon.png">. Theses pictures range from 57x57 to 152x152. See Apple specs for full reference.
Even if you find no Apple touch icon declaration, try to load them anyway, based on Apple naming convention. For example, you might find something at /apple-touch-icon.png. Again, see Apple specs for reference.
Look for high definition PNG favicon in the code, such as <link rel="icon" type="image/png" href="/favicon-196x196.png" sizes="196x196">. In this example, you have a 196x196 picture.
Look for Windows 8 / IE10 and Windows 8.1 / IE11 tile pictures, such as <meta name="msapplication-TileImage" content="/mstile-144x144.png">. These pictures range from 70x70 to 310x310, or even more. See these Windows 8 and Windows 8.1 references.
Look for /browserconfig.xml, dedicated to Windows 8.1 / IE11. This is the other place where you can find tile pictures. See Microsoft specs.
Look for the og:image declaration such as <meta property="og:image" content="http://somesite.com/somepic.png"/>. This is how a web site indicates to FB/Pinterest/whatever the preferred picture to represent it. See Open Graph Protocol for reference.
At this point, you found no suitable logo... damned! You can still load all pictures in the page and make a guess to pick the best one.

    :param source:
    :param url:
    :return:
    """
    parsed_site_uri = parse_url(url=url)

    soup = BeautifulSoup(source, 'html.parser')

    favicon_url = try_to_get_from_og(soup=soup)
    if favicon_url is not None:
        print "found og favicon"
        return favicon_url
    favicon_url = try_to_get_from_source(soup=soup, rel='apple-touch-icon', parsed_site_uri=parsed_site_uri)
    if favicon_url is not None:
        print "found apple-touch-icon from source"
        return favicon_url
    favicon_url = try_to_get_favicon(parsed_site_uri=parsed_site_uri,icon_path="apple-touch-icon.png")
    if favicon_url is not None:
        print "found apple-touch-icon.png"
        return favicon_url
    favicon_url = try_to_get_from_source(soup=soup, rel='icon', parsed_site_uri=parsed_site_uri)
    if favicon_url is not None:
        print "found icon from source"
        return favicon_url
    favicon_url = try_to_get_favicon(parsed_site_uri=parsed_site_uri,icon_path="favicon.ico")
    if favicon_url is not None:
        print "found favicon.ico"
        return favicon_url
    return None


def try_to_get_from_og(soup):
    image = soup.find("meta", property="og:image")
    if image and image.has_attr("content"):
        favicon_url = image['content']
        return favicon_url
    return None


def try_to_get_from_source(soup,rel,parsed_site_uri):
    icon_link = soup.find('link', rel=rel)
    if icon_link and icon_link.has_attr('href'):
        favicon_url = icon_link['href']
        # Sometimes we get a protocol-relative path
        if favicon_url.startswith('//'):
            favicon_url = parsed_site_uri.scheme + ':' + favicon_url

        # An absolute path relative to the domain
        elif favicon_url.startswith('/'):
            favicon_url = parsed_site_uri.scheme + '://' + \
                          parsed_site_uri.netloc + favicon_url

        # A relative path favicon
        elif not favicon_url.startswith('http'):
            path, filename = os.path.split(parsed_site_uri.path)
            favicon_url = parsed_site_uri.scheme + '://' + \
                          parsed_site_uri.netloc + '/' + os.path.join(path, favicon_url)

        return favicon_url
    return None


def save_favicon(url):
    """
    Returns a favicon URL for the URL passed in. We look in the markup returned
    from the URL first and if we don't find a favicon there, we look for the
    default location, e.g., http://example.com/favicon.ico . We retrurn None if
    unable to find the file.

    Keyword arguments:
    url -- A string. This is the URL that we'll find a favicon for.

    Returns:
    The URL of the favicon. A string. If not found, returns None.
    """

    favicon_url = get_favicon_url(url=url)
    parsed_site_uri = urlparse(url)
    if favicon_url is not None:
        r = requests.get(favicon_url, headers=headers, stream=True)
        ext = r.url.split("/")[-1].split(".")[-1]
        filename = parsed_site_uri.netloc.replace(".","_") + "."+ ext
        if r.status_code == requests.codes.ok:
            with open("/tmp/"+filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
    return None




def get_favicon_url(url):
    favicon_url = None
    # Get the markup
    try:
        response = requests.get(url, headers=headers)
    except:
        raise Exception("Unable to find URL. Is it valid? %s" % url)

    if response.status_code == requests.codes.ok:
        favicon_url = find_best_favicon_url(response.content, url)
    return favicon_url


def try_to_get_favicon(parsed_site_uri,icon_path):
    prefix_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_site_uri)
    favicon_url = prefix_url+icon_path
    try:
        response = requests.get(favicon_url)
    except:
        return None
    if response.status_code != requests.codes.ok:
        return None
    return favicon_url


save_favicon("http://www.zalando.it")