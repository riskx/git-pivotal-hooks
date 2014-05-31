#!/usr/bn/env python

"""
Copyright (c) 2011 Socialize, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.  

"""

import urllib2
import sys
import os.path
import re
import json


def load_config():
    pivotal_items = {}
    with open(".pivrc") as f:
        for line in f:
            text = re.split(":\s+", line.strip())
            pivotal_items[text[0]] = text[1]
    return pivotal_items['token'], pivotal_items['filter'], pivotal_items['project_id']


def load_document(token, filter, project_id):
    req_url = 'https://www.pivotaltracker.com/services/v5/projects/%s/search?query=%s' % (project_id, filter)
    print "calling %s" % (req_url)
    req = urllib2.Request(req_url)
    req.add_header("X-TrackerToken", token)
    result = urllib2.urlopen(req)
    return result

if __name__ == '__main__':

    if not os.path.isfile(".pivrc"):
        sys.exit()

    files = sys.argv[0]
    msg_file = sys.argv[1]

    token, filter, project_id = load_config()
    res = load_document(token, filter, project_id)
    pivotal_document = json.load(res)

    #print "pivotal_document: \n %s" %(pivotal_document)
    stories = pivotal_document['stories']['stories']

    stories_to_add = []
    actions_to_add = []
    potential_stories_to_add = []
    if stories:
        i = 1
        print "Available Stories"
        for story in stories:
            id = story['id']
            name = story['name']

            print "%s: %s -- %s" % (i, id, name)
            potential_stories_to_add.append((id, name))

            i += 1
    else:
        print "No stories found. Not adding anything to commit message."
        sys.exit()

    sys.stdin = open('/dev/tty')
    items_to_include = re.split(",s*", raw_input(
        "Please choose which story/stories this commit relates to (as a comma separated list):"))
    items_to_include = [i.strip() for i in items_to_include if i]

    print "items_to_include %s" % (items_to_include)
    if items_to_include:
        for i in items_to_include:
            if any(i in s for s in ['fixed','fixes','finished']):
                actions_to_add.append(i)
            else:
                index = int(i) - 1
                if index < len(potential_stories_to_add):
                    stories_to_add.append(potential_stories_to_add[index])
                else:
                    print "Sorry, %s was not an option." % i

    if len(stories_to_add) == 0:
        print "No stories found. Not adding anything to commit message."
        sys.exit()

    stringified_stories = ['#%s' % story[0] for story in stories_to_add]

    msg = open(msg_file, 'r').read()
    msg = '[%s %s] %s' % (' '.join(actions_to_add), ' '.join(stringified_stories), msg)
    open(msg_file, 'w').write(msg)
