from datetime import datetime
from documents.models import Company, Person, Project, DocumentVersion, Document
import requests
import xml.etree.ElementTree as ET

username = 'brycegroff'
password = 'maddog'
service = 'https://ndptc.basecamphq.com'


def import_groups():
    r = requests.get('%s/companies.xml' % service, auth=(username, password))
    if r.status_code != 200:
        return r.status_code
    xml = ET.fromstring(r.text)
    for company in xml.findall('company'):
        name = company.find('name').text
        address = company.find('address-one').text
        address1 = company.find('address-two').text
        country = company.find('country').text
        if country != 'United States':
            print 'Something is up: %s' % country
        country = 'US'
        city = company.find('city').text
        state = company.find('state').text
        bc_id = company.find('id').text
        locale = company.find('locale').text
        print locale
        fax = company.find('phone-number-fax').text
        phone = company.find('phone-number-office').text
        web = company.find('web-address').text
        timezone = company.find('time-zone-id').text
        if timezone == 'Hawaii':
            timezone = 'Pacific/Honolulu'
        else:
            timezone = 'Pacific/Honolulu'
        Company.objects.create(name=name, address=address, address1=address1, country=country, city=city, state='HI',
                               bc_id=bc_id, locale=locale, fax=fax, phone=phone, website=web, timezone=timezone)


def import_users():
    r = requests.get('%s/people.xml' % service, auth=(username, password))
    if r.status_code != 200:
        return r.status_code
    xml = ET.fromstring(r.text)
    for person in xml.findall('person'):
        p = Person()
        p.date_joined = datetime.strptime(person.find('created-at').text, '%Y-%m-%dT%H:%M:%SZ')
        p.is_active = person.find('deleted').text
        p.access_new_projects = True if person.find('has-access-to-new-projects').text == 'true' else False
        p.bc_id = person.find('id').text
        p.im_handle = person.find('im-handle').text
        p.im_service = person.find('im-service').text
        p.fax = person.find('phone-number-fax').text
        p.home = person.find('phone-number-home').text
        p.mobile = person.find('phone-number-mobile').text
        p.office = person.find('phone-number-office').text
        p.ext = person.find('phone-number-office-ext').text
        p.title = person.find('title').text
        p.last_updated = datetime.strptime(person.find('updated-at').text, '%Y-%m-%dT%H:%M:%SZ')
        p.first_name = person.find('first-name').text
        p.last_name = person.find('last-name').text
        p.company = Company.objects.get(bc_id=person.find('company-id').text)
        p.timezone = person.find('time-zone-name').text
        p.username = person.find('user-name').text
        p.is_superuser = True if person.find('administrator').text == 'true' else False
        p.email = person.find('email-address').text
        p.avatar_url = person.find('avatar-url').text

        if p.username is None:
            p.username = p.email
        if len(p.username) >= 29:
            print 'username: %s' % p.username
        if len(p.first_name) >= 29:
            print 'firstname'
        if len(p.last_name) >= 29:
            print 'last_name'
        p.save()


def import_projects():
    r = requests.get('%s/projects.xml' % service, auth=(username, password))
    if r.status_code != 200:
        return r.status_code
    xml = ET.fromstring(r.text)
    for project in xml.findall('project'):
        p = Project()
        p.name = project.find('name').text
        p.bc_id = project.find('id').text
        if project.find('last-changed-on').text is not None:
            p.changed = datetime.strptime(project.find('last-changed-on').text, '%Y-%m-%dT%H:%M:%SZ')
        p.created = datetime.strptime(project.find('created-on').text, '%Y-%m-%d')
        p.is_active = project.find('status').text
        p.owner = Company.objects.get(bc_id=project.find('company').find('id').text)
        p.save()


def import_documents(project_id):
    r = requests.get('%s/projects/%s/attachments.xml' % (service, project_id), auth=(username, password))
    if r.status_code != 200:
        return r.status_code
    xml = ET.fromstring(r.text);
    i = 1
    for document in xml.findall('attachment'):
        d = DocumentVersion()
        d.bc_id = document.find('id').text
        d.created = datetime.strptime(document.find('created-on').text, '%Y-%m-%dT%H:%M:%SZ')
        d.bc_size = document.find('byte-size').text
        d.bc_category = document.find('category-id').text
        d.bc_collection = document.find('collection').text
        d.bc_latest = True if document.find('current').text == 'true' else False
        d.description = document.find('description').text
        d.bc_name = document.find('name').text
        try:
            d.bc_person = Person.objects.get(bc_id=document.find('person-id').text)
        except Person.DoesNotExist:
            d.bc_person = None
        d.bc_project = Project.objects.get(bc_id=document.find('project-id').text)
        d.bc_url = document.find('download-url').text
        d.save()


def create_document_from_document_version(document_version):
    assert type(document_version) is DocumentVersion, 'The parameter must be of type DocumentVersion'
    document = Document.objects.create(name=document_version.name, mime=None, project=document_version.bc_project)
    for document_version in DocumentVersion.objects.filter(bc_collection=document_version.bc_collection):
        document_version.document = document
        document_version.save()
