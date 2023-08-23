import dotenv
from quart import Quart, jsonify, routing, request
from quart_cors import cors
import os

dotenv.load_dotenv('.env')

app = Quart(__name__)

app.config['QUART_DEBUG'] = os.environ.get('QUART_DEBUG')
app.config['QUART_ENV'] = os.environ.get('QUART_ENV')
app.secret_key = 'some_key'

app = cors(
    app,
    allow_origin=['http://127.0.0.1:5500'],
    allow_headers=['content-type'],
    allow_credentials=True
)

@app.route('/tracking/js', methods=['post'])
async def receive(**kwargs):
    data = await request.form
    print(data)
    return jsonify({})


if __name__ == '__main__':
    app.run(debug=True)
