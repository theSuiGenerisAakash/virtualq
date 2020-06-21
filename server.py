from flask import Flask, request, render_template
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from twilio.rest import Client
import os
from random import randint

sms_client = None
source_phone_no = None
db_client = None

app = Flask(__name__, template_folder='pages')

def setup_sms_client():
    global sms_client, source_phone_no
    sms_client = Client(os.environ.get('ACCOUNT_SID'), os.environ.get('AUTH_TOKEN'))
    source_phone_no = os.environ.get('SOURCE_NO')

def setup_storage_client():
    global db_client
    db_string = f"postgres://{os.environ.get('DB_USER')}:{os.environ.get('DB_PWD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    db_client = create_engine(db_string)

def send_otp(user_contact, generated_otp):
    sms_client.messages.create(to=user_contact, from_=source_phone_no, body=f"Hello! Your login  OTP is {generated_otp}", force_delivery=True)

def send_confirmation(user_contact):
    sms_client.messages.create(to=user_contact, from_=source_phone_no, body=f"Congrats! Your place is reserved!", force_delivery=True)

@app.route('/business/<url_endpoint>', methods=['GET'])
def get_business_queue_reg_page(url_endpoint):
    response, status = '', 500
    try:
        retrieved_url = db_client.execute(text(f'''SELECT id, name, url, phone_no FROM public.business WHERE url LIKE '%{url_endpoint}';''')).fetchone()
        if retrieved_url is None:
            status = 404
            raise Exception('No business found!')
        else:
            id, name, url, phone_no = retrieved_url[0], retrieved_url[1], retrieved_url[2], retrieved_url[3]
            queues = db_client.execute(f'''SELECT name, queue_id FROM public.business_queue WHERE business_id='{id}';''').fetchall()
            if len(queues) == 0:
                raise Exception('No registered queues found')
            else:
                queues_parsed = [{'name': x[0], 'id': x[1]} for x in queues]
                status = 200
                return render_template('register_queue.html', business={'name': name, 'phone_no': phone_no, 'queue': queues_parsed})
    except Exception as e:
        response = str(e)
        return render_template('404.html', message=response)

@app.route('/admin/business', methods=['POST'])
def admin_business():
    response, status = '', 500
    try:
        db_client.execute(f'''INSERT INTO public.business({f", ".join(request.form.keys())}) VALUES ({", ".join(map(lambda x: f"'{x}'",request.form.values()))})''');
        response='Business account created!'
        status = 201
    except Exception as e:
        print(e)
    finally:
        return app.make_response(response), status

@app.route('/admin/business/queue', methods=['POST'])
def add_queue_for_busines():
    response, status = '', 500
    try:
        business_id, = db_client.execute(f'''SELECT id FROM public.business WHERE name='{request.form.get(f"business_name")}';''').fetchone();
        queue_type_id, = db_client.execute(f'''SELECT id FROM public.queue_type WHERE type='{request.form.get(f"queue_type")}';''').fetchone();
        queue_name = request.form.get('queue_name');
        queue_length = request.form.get('queue_length');
        result = db_client.execute(f'''INSERT INTO public.business_queue (business_id, queue_id, name, max_queue_length) VALUES ('{business_id}', '{queue_type_id}', '{queue_name}', '{queue_length}') RETURNING *;''').fetchone();
        db_client.execute(f'''INSERT INTO public.queue_status (business_queue_id) VALUES ('{result[0]}')''');
        response=f'Queue created with name: {request.form.get(f"queue_name")} for business: {request.form.get(f"business_name")}'
        status = 201
    except Exception as e:
        print(e)
    finally:
        return app.make_response(response), status

@app.route('/register', methods=['POST'])
def register_customer():
    response, status = '', 500
    try:
        req_phone_no = request.form.get("phone_no")
        req_name = request.form.get("name")
        req_business_queue_id = request.form.get("business_queue_id")
        otp = randint(100000, 999999)
        if db_client.execute(f'''SELECT id FROM public.customer WHERE phone_no='{req_phone_no}';''').fetchone() is not None:
            result = db_client.execute(f'''UPDATE public.customer SET name='{req_name}' WHERE phone_no='{req_phone_no}' RETURNING *;''').fetchone();
        else:
            result = db_client.execute(f'''INSERT INTO public.customer (name, phone_no) VALUES ('{req_name}', '{req_phone_no}') RETURNING *;''').fetchone();
        customer_id = result[0]
        send_otp(req_phone_no, otp)
        if db_client.execute(f'''SELECT * FROM public.customer_queue WHERE customer_id='{customer_id}' AND business_queue_id='{req_business_queue_id}';''').fetchone() is None:
            db_client.execute(f'''INSERT INTO customer_queue (customer_id, business_queue_id, otp) VALUES ('{customer_id}', '{req_business_queue_id}', '{otp}');''')
        else:
            db_client.execute(f'''UPDATE customer_queue SET otp='{otp}' WHERE customer_id='{customer_id}' AND business_queue_id='{req_business_queue_id}';''')
        response='OTP sent!'
        status = 201
    except Exception as e:
        print(e)
        response = str(e)
    finally:
        return app.make_response(response), status

@app.route('/verify', methods=['POST'])
def verify_registration():
    response, status = '', 500
    try:
        req_phone_no = request.form.get("phone_no")
        req_business_queue_id = request.form.get("business_queue_id")
        customer_id, = db_client.execute(f'''SELECT id FROM public.customer WHERE phone_no='{req_phone_no}';''').fetchone()
        if customer_id is not None:
            otp, = db_client.execute(f'''SELECT otp FROM public.customer_queue WHERE customer_id='{customer_id}' AND business_queue_id='{req_business_queue_id}';''').fetchone();
            if otp == request.form.get('otp'):
                db_client.execute(f'''UPDATE public.customer_queue SET is_registered=true WHERE customer_id='{customer_id}' AND business_queue_id='{req_business_queue_id}';''')
                result = db_client.execute(f'''UPDATE public.queue_status SET queue = array_append(queue, '{customer_id}') WHERE business_queue_id='{req_business_queue_id}' RETURNING *;''').fetchone()
                business_name, = db_client.execute(f'''SELECT b.name FROM business INNER JOIN business_queue bq ON b.id=bq.business_id where bq.business_queue_id='{req_business_queue_id}';''').fetchone()
                send_confirmation(req_phone_no, position)
                return render_template('registered.html', queue={'queue_status_id': result[0], 'queue_length': len(result[2]), 'business_name': business_name})
            else:
                status = 403
                raise Exception('Incorrect OTP provided!')
        else:
            status = 401
            raise Exception('Unregistered user!');
    except Exception as e:
        print(e)
        response = str(e)
        return app.make_response(response), status

if __name__ == '__main__':
    load_dotenv()
    setup_sms_client()
    setup_storage_client()
    app.run(port=8080, debug=True)
