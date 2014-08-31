# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.conf import settings
from django.templatetags.static import static

import collections
import json
import urllib2

# Cache the JSON encodings for some rarely changing data here.
policymaker_json = None
category_json = None
district_json = None

def get_js_paths():
    prefix = getattr(settings, 'URL_PREFIX', '')
    debug = "true" if settings.DEBUG else "false"
    return {
        'API_PREFIX': '/' + prefix,
        'GEOCODER_API_URL': settings.GEOCODER_API_URL,
        'DEBUG': debug
    }

def get_metadata(request, info):
    props = []
    props.append({'name': 'og:image', 'content': request.build_absolute_uri(static('img/share-image-154x154.png'))})
    if 'description' in info:
        props.append({'name': 'og:description', 'content': info['description']})
    if 'title' in info:
        props.append({'name': 'og:title', 'content': info['title']})
    props.append({'name': 'og:url', 'content': request.build_absolute_uri(request.path)})
    return {'meta_properties': props}

def render_view(request, template, args={}):
    args.update(get_js_paths())
    args.update(get_metadata(request, args))
    return render_to_response(template, args)

def get_policymakers(request):
    global policymaker_json

    if policymaker_json is None:
        policymaker_json = json.load(urllib2.urlopen("%s/policymaker/filter/?abbreviation.isnull=false" % settings.KLUPUNG_API_URL))["objects"]
    return json.dumps(policymaker_json)

def get_categories(request):
    global category_json

    if category_json is None:
        category_json = json.load(urllib2.urlopen("%s/category/filter/?level.lte=1" % settings.KLUPUNG_API_URL))["objects"]
    return json.dumps(category_json)

def get_districts(request):
    return '[]'

def home_view(request):
    args = {'pm_list_json': get_policymakers(request)}
    args['title'] = 'Jyväskylän kaupungin Päätökset-palvelu'
    args['description'] = 'Löydä juuri sinua kiinnostavat Jyväskylän kaupungin poliittiset päätökset.'
    return render_view(request, 'home.html', args)

def issue_view(request, template, args={}):
    args['cat_list_json'] = get_categories(request)
    args['pm_list_json'] = get_policymakers(request)
    args['district_list_json'] = get_districts(request)

    return render_view(request, template, args)

def issue_list(request):
    args = {'title': 'Asiat', 'description': 'Hae kaupungin päätöksiä.'}
    return issue_view(request, 'issue.html', args)
def issue_list_map(request):
    args = {'title': 'Asiat kartalla', 'description': 'Tarkastele kaupungin päätöksiä kartalla.'}
    return issue_view(request, 'issue.html')

def issue_details(request, slug, pm_slug=None, year=None, number=None):
    issue_json_list = json.load(urllib2.urlopen("%s/issue/filter/?slug.eq=%s" % (settings.KLUPUNG_API_URL, urllib2.quote(slug))))["objects"]
    issue_json = issue_json_list[0]

    args = {}

    args['title'] = issue_json["subject"]
    summary = ""

    if summary:
        # Get first sentences
        s = summary.split('.')
        desc = '.'.join(s[0:3])
        args['description'] = desc + '.'

    args['issue_json'] = json.dumps(issue_json)

    ai_list_json = json.load(urllib2.urlopen("%s/agenda_item/filter/?issue__id.eq=%d" % (settings.KLUPUNG_API_URL, issue_json["id"])))["objects"]
    args['ai_list_json'] = json.dumps(ai_list_json)

    return issue_view(request, 'issue.html', args)

def policymaker_view(request, template, args={}):
    args['pm_list_json'] = get_policymakers(request)

    return render_view(request, template, args)

def policymaker_list(request):
    return policymaker_view(request, 'policymaker.html')

Policymaker = collections.namedtuple("Policymaker", ("name", "summary"))

def policymaker_details(request, slug, year=None, number=None):
    pm_json_list = json.load(urllib2.urlopen("%s/policymaker/filter/?slug.eq=%s" % (settings.KLUPUNG_API_URL, urllib2.quote(slug))))["objects"]
    pm_json = pm_json_list[0]
    pm = Policymaker(name=pm_json["name"], summary=pm_json["summary"])
    args = {}
    args['policymaker'] = pm
    if year:
        args['meeting_year'] = year
        args['meeting_number'] = number
    return policymaker_view(request, 'policymaker.html', args)

def about(request):
    return render_view(request, "about.html")
