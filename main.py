import re
import json
import time
import requests
from appwrite import query
import os
import h2o_wave
from h2o_wave import main, app, Q, ui, pack
import appwrite

from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.databases import Databases
from appwrite.services.account import Account
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.id import ID
from dotenv import load_dotenv
load_dotenv()
# Appwrite REST setup
client = Client()
client.set_endpoint(os.getenv("PROJECT_ENDPOINT")) # Cloud instance
client.set_project(os.getenv("PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))
client.set_self_signed()
Query = query.Query()

databases = Databases(client)
users = Users(client)
store_name = ''
phone = ''
country = ''
facebook = ''
instagram = ''
whatsapp = ''
website = ''

database_id = os.getenv("DATABASE_CONTACTS")  # contacts cloud
collection_bgc_id = os.getenv("COLLECTIONS_BGC")  # bigcommerce customers cloud
document_id = None
user_id = None




#global document_id
# Appwrite List documents
response = databases.list_documents(
    database_id,
    collection_bgc_id,
    [
        Query.order_desc('bigc_id'),
        Query.not_equal('notes', ''),
        Query.limit(50) # Between 1 and 50. Match this value on 'content'
    ]
         )
customers = response['documents']
total_data = []

# Scrap customers 'notes' for data extraction
count = 0
for customer in customers:
    id_ = str(customer['$id'])
    text = customer['notes']
    store_name = ''
    address = ''
    phone = ''
    country = ''
    facebook = ''
    instagram = ''
    whatsapp = ''
    website = ''
    store_names = re.findall(r'(?:StoreName|Store Name|SName|doingBusinessAs): (.*?)\n', text, re.IGNORECASE)
    addresses = re.findall(r'(?:Addr): (.*?)\n', text, re.IGNORECASE)
    phones = re.findall(r'(?:Phone|Tel): (.*?)\n', text, re.IGNORECASE)
    facebooks = re.findall(r'(?:Facebook|facebook): (.*?)\n', text, re.IGNORECASE)
    instagrams = re.findall(r'(?:Instagram|instagram): (.*?)\n', text, re.IGNORECASE)
    websites = re.findall(r'(?:Website|website): (.*?)\n', text, re.IGNORECASE)
    whatsapps = re.findall(r'(?:WhatsApp|Whatsapp|WA): (.*?)\n', text, re.IGNORECASE)
    countries = re.findall(r'(?:Country|CT): (.*?)\n', text, re.IGNORECASE)

    for match in store_names:
        if address in addresses:
            if address in match:
                store_name = match.replace(address,'')
        else:
            store_name = match
    for match in phones:
        if customer['phone'] != '':
            phone = customer['phone']
        else:
            phone = match
            print('Match Found for Phone: ', phone)
    for match in facebooks:
        print('fb is ', match)
        if match == 'None':
            continue
        elif 'https://www.facebook.com/' not in match:
            facebook = 'https://www.facebook.com/' + match
        else:
            facebook = match
    for match in instagrams:
        print('ig is ', match)
        if match == 'None':
            continue
        elif 'https://www.instagram.com/' not in match:
            instagram = 'https://www.instagram.com/' + match
        else:
            instagram = match
    for match in websites:
        if match == 'None':
            continue
        elif 'https://' not in match:
            website = 'https://' + match
        else:
            website = match
    for match in whatsapps:
        whatsapp = match
    for match in countries:
        country = match

    # Prepare patch data
    update = {}
    update_data = {}

    update['store_name'] = store_name
    update['phone'] = phone
    update['country'] = country
    if facebook:
        update['facebook'] = facebook
    else:
        update['facebook'] = None
    if instagram:
        update['instagram'] = instagram
    else:
        update['instagram'] = None
    update['whatsapp'] = whatsapp
    if website:
        update['website'] = website
    else:
        update['website'] = None
    update_data = json.dumps(update)
    total_data.append(update)
    print("UPDATE IS: " + id_, update)
    if update['store_name']:
        try:
            update_response = databases.update_document(
                database_id,
                collection_bgc_id,
                document_id=str(customer['$id']),
                data=update_data
            )
            time.sleep(1)
            count += 1
            print('Customers processed: ', count)
            print('Check the following note if the script breaks. You will find why')
            print(update_response)
            up_responses = update_response
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
    else:
        print('Nothing to do here')
print("Done!")


#h2o_wave app here
@app('/customers')
async def serve(q: Q):
    q.page.drop()
    q.page['content'].content.data.customers = customers
    q.page['updates'].content.data.updates = total_data

    content = '''
        <br>
        <h2>Scraping 50 last customers</h2> 
        <div style="width:80%">
        {{#each customers}}
            {{#if notes}}
            <h4>Scraping company: {{'company'}}</h4>
            <p>BigCommerce ID: {{'bigc_id'}}</p>
            <p>Notes: {{'notes'}}</p>
            {{/if}}
        {{/each}}
        </div>
        '''
    # Match the numeric value with Query.limit.
    note_update = '''
        <div style="width:80%">
        {{#each updates}}
            {{#if store_name}}
            <p>BigCommerce ID: {{bigc_id}}</p>
            <p>Store Name: {{store_name}}</p>
            <p>Phone: {{phone}}</p>
            <p>Country: {{country}}</p>
            <p>Facebook: {{facebook}}</p>
            <p>Instagram: {{instagram}}</p>
            <p>WhatsApp: {{whatsapp}}</p>
            <p>Website: {{website}}</p>
            <hr>
            {{/if}}
        {{/each}}
        </div>
        '''

    # Modify the page
    q.page['meta'] = ui.meta_card(box='', layouts=[
        ui.layout(
            # If the viewport width >= 0:
            breakpoint='xs',
            zones=[
                # 80px high header
                ui.zone('header', size='80px'),
                # Use remaining space for content
                ui.zone('content'),
                ui.zone('updates')
            ]
        ),
        ui.layout(
            # If the viewport width >= 768:
            breakpoint='m',
            zones=[
                # 80px high header
                ui.zone('header', size='80px'),
                # Use remaining space for body
                ui.zone('body', direction=ui.ZoneDirection.ROW, zones=[
                    # 250px wide sidebar
                    ui.zone('sidebar', size='250px'),
                    # Use remaining space for content
                    ui.zone('content'),
                ]),
                ui.zone('updates'),
                ui.zone('footer'),
            ]
        ),
        ui.layout(
            # If the viewport width >= 1200:
            breakpoint='xl',
            width='1200px',
            zones=[
                # 80px high header
                ui.zone('header', size='80px'),
                # Use remaining space for body
                ui.zone('body', direction=ui.ZoneDirection.ROW, zones=[
                    # 300px wide sidebar
                    # ui.zone('sidebar', size='300px'),
                    ui.zone('content'),
                    # Use remaining space for other widgets
                    # ui.zone('other', zones=[
                    #     ui.zone('content'),
                    # ]),
                ]),
                ui.zone('updates'),
                ui.zone('footer'),
            ]
        )
    ])
    q.page['header'] = ui.header_card(
        # Place card in the header zone, regardless of viewport size.
        box='header',
        title='Populate Customer Fields from Notes',
        subtitle='On ZJ Events Appwrite Cloud deployment',
        nav=[
            ui.nav_group('Menu', items=[
                ui.nav_item(name='#menu/customers', label='Customers'),
            ]),
            ui.nav_group('Help', items=[
                ui.nav_item(name='#about', label='About'),
                ui.nav_item(name='#support', label='Support'),
            ])
        ],
    )
    q.page['content'] = ui.template_card(
        box=ui.boxes(
            # If the viewport width >= 0, place as fourth item in content zone.
            ui.box(zone='content', order=3),
            # If the viewport width >= 768, place as third item in content zone.
            ui.box(zone='content', order=2),
            # If the viewport width >= 1200, place in content zone.
            # 'content',
            ui.box(zone='content'),
        ),
        title='Progress',
        content=content,
        data=pack(dict(customers=customers))
    )
    q.page['updates'] = ui.template_card(
        box=ui.boxes(
            # If the viewport width >= 0, place as fourth item in content zone.
            ui.box(zone='updates'),
            # If the viewport width >= 768, place as third item in content zone.
            ui.box(zone='updates'),
            # If the viewport width >= 1200, place in content zone.
            # 'content',
            ui.box(zone='updates'),
        ),
        title='Results',
        content=note_update,
        data=pack(dict(updates=total_data))
    )
    q.page['footer'] = ui.footer_card(box='footer', caption='(c) 2023-2030 ZJ Events, LLC. ')
    # Save the page
    await q.page.save()

