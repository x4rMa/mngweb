import requests

from datetime import datetime
from django.conf import settings
from django.utils.http import urlquote

from urllib.parse import urljoin

from .forms import ProjectLineForm


PROJECT_DJANGO_TO_LIMSFM_MAP = {
    'uuid': 'uuid',
    'all_content_received_date': 'all_content_received_date',
    'contact_name_full': 'Contact::name_full',
    'data_sent_date': 'data_sent_date',
    'meta_data_status': 'meta_data_status',
    'projectline_count': 'unstored_projectline_count',
    'modal_queue_name': 'unstored_modal_queue_name',
    'reference': 'reference',
    'results_path': 'results_path',
    'sample_sheet_url': 'sample_sheet_url',
    'wait_time_weeks': 'unstored_wait_time_weeks',
}

PROJECT_LIMSFM_TO_DJANGO_MAP = {
    v: k for k, v in PROJECT_DJANGO_TO_LIMSFM_MAP.items()}

PROJECTLINE_DJANGO_TO_LIMSFM_MAP = {
    'uuid': 'uuid',
    'aliquottype_name': 'Aliquot::unstored_aliquottype_name',
    'collection_day': 'Sample::collection_day',
    'collection_month': 'Sample::collection_month',
    'collection_year': 'Sample::collection_year',
    'container_position': 'Aliquot::unstored_container_position',
    'container_ref': 'Container::reference',
    'customers_ref': 'Sample::customers_ref',
    'dna_concentration_ng_ul': 'Aliquot::dna_concentration_ng_ul',
    'environmental_sample_type': 'Sample::environmental_sample_type',
    'further_details': 'Sample::further_details',
    'geo_country': 'Sample::geo_country_iso2_id',
    'geo_country_name': 'sample_Country::name',
    'geo_specific_location': 'Sample::geo_specific_location',
    'host_sample_type': 'Sample::host_sample_type',
    'host_taxon': 'Sample::host_taxon_id',
    'host_taxon_name': 'sample_Taxon#host::name',
    'lab_experiment_type': 'Sample::lab_experiment_type',
    'queue_name': 'Queue::name',
    'sample_ref': 'Sample::reference',
    'study_type': 'Sample::study_type',
    'taxon': 'Sample::taxon_id',
    'taxon_name': 'Taxon::name',
    'volume_ul': 'Aliquot::volume_ul',
    'well_alpha': 'Aliquot::unstored_well_position_display',
}

PROJECTLINE_LIMSFM_TO_DJANGO_MAP = {
    v: k for k, v in PROJECTLINE_DJANGO_TO_LIMSFM_MAP.items()}


def projectline_to_fm_dict(project_uuid, cleaned_data):
    """Convert dict data returned by a ProjectLineForm to a
       dict suitable to be used as a Filemaker RESTfm payload"""

    # Objects -> filemaker ids
    taxon = cleaned_data.pop('taxon_name', None)
    if taxon:
        cleaned_data['taxon'] = taxon.fm_id

    host_taxon = cleaned_data.pop('host_taxon_name', None)
    if host_taxon:
        cleaned_data['host_taxon'] = host_taxon.fm_id

    geo_country = cleaned_data.pop('geo_country_name', None)
    if geo_country:
        cleaned_data['geo_country'] = geo_country.iso2

    # Construct dict
    fm_data = {}
    for k, v in cleaned_data.items():
        if k in PROJECTLINE_DJANGO_TO_LIMSFM_MAP:
            fm_data[PROJECTLINE_DJANGO_TO_LIMSFM_MAP[k]] = str(v) if v else ''
    fm_data['Project::uuid_validation'] = project_uuid

    return fm_data


def limsfm_request(rel_uri, method='get', params={}, json=None):
    """Send an API request to LIMSfm (RESTfm).
       Returns a response object or raises an exception"""

    params['RFMkey'] = settings.RESTFM_KEY
    uri = (
        "%(base)s%(rel_uri)s.json" %
        {'base': settings.RESTFM_BASE_URL, 'rel_uri': rel_uri}
    )
    s = requests.Session()
    prepped_request = requests.Request(
        method, uri, params=params, json=json).prepare()
    response = s.send(prepped_request, timeout=5)
    response.raise_for_status()

    return response


def limsfm_get_project(uuid):
    """Return a Project dictionary, including ProjectLines, from LIMSfm"""

    uri = ('layout/project_api/%(field)s%(value)s' %
           {
               'field': urlquote('uuid==='),
               'value': urlquote(uuid)
           })
    project_response = limsfm_request(uri, 'get')
    project_raw = project_response.json()['data'][0]
    lines_response = limsfm_request('layout/projectline_api', 'get', {
        'RFMsF1': 'project_id',
        'RFMsV1': project_raw['project_id'],
        'RFMmax': 0
    })
    projectlines_raw = lines_response.json()['data']

    # Map filemaker project keys to django keys
    project = {}
    for d, f in PROJECT_DJANGO_TO_LIMSFM_MAP.items():
        if f in project_raw:
            project[d] = project_raw[f]

    # Transformations
    if project['results_path']:
        project['results_url'] = urljoin(
            settings.MNGRESULTS_BASE_URL,
            project['results_path'] + '/data.html')

    if project['all_content_received_date']:
        date = project['all_content_received_date']
        date = datetime.strptime(date, '%m/%d/%Y').strftime('%d-%b-%Y')
        project['all_content_received_date'] = date

    if project['data_sent_date']:
        date = project['data_sent_date']
        date = datetime.strptime(date, '%m/%d/%Y').strftime('%d-%b-%Y')
        project['data_sent_date'] = date

    # Map filemaker projectline keys to django keys
    project['modal_queue_matches'] = 0
    projectlines = []
    for pl in projectlines_raw:
        data = {}
        for d, f in PROJECTLINE_DJANGO_TO_LIMSFM_MAP.items():
            if f in pl:
                data[d] = pl[f]
        data['form'] = ProjectLineForm(initial=data)
        if data['queue_name'] == project['modal_queue_name']:
            project['modal_queue_matches'] += 1
        projectlines.append(data)

    # Sort the projectlines and append to list project dict
    projectlines.sort(
        key=lambda k: (
            k['container_ref'],
            int(k['container_position'])
            if len(k['container_position']) else 0,
            k['sample_ref'],
        )
    )
    project['projectlines'] = projectlines

    return project


def limsfm_update_projectline(project_uuid, projectline_uuid, cleaned_data):
    """Update a single LIMSfm ProjectLine"""

    json = {'data': [projectline_to_fm_dict(project_uuid, cleaned_data)]}
    uri = ('layout/projectline_api/%(field)s%(value)s' %
           {
               'field': urlquote('uuid==='),
               'value': urlquote(projectline_uuid)
           })
    return limsfm_request(uri, 'put', json=json)


def limsfm_bulk_update_projectlines(project_uuid, projectlines):
    """Update LIMSfm ProjectLines in bulk"""

    json = {'meta': [], 'data': []}

    for k, v in projectlines.items():
        json['meta'].append({'recordID': ('uuid===%s' % k)})
        json['data'].append(projectline_to_fm_dict(project_uuid, v))

    return limsfm_request('bulk/projectline_api', 'put', json=json)


def limsfm_email_project_links(email_address):
    """Call a script to email project links to contact"""
    uri = 'script/contact_email_project_links/REST'
    return limsfm_request(uri, 'get', params={'RFMscriptParam': email_address})
