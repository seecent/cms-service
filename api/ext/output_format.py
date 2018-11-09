
from __future__ import absolute_import
import hug


@hug.format.content_type('application/xml')
def output_xml(content, request=None, response=None):
    return str(content).encode('utf8')
