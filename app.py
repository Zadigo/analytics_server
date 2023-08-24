import asyncio
import csv
import dataclasses
import datetime
import json
import os
from dataclasses import dataclass, field
from functools import cached_property
from queue import Queue
from typing import OrderedDict

import dotenv
import pytz
from quart import Quart, jsonify, request, routing
from quart_cors import cors

dotenv.load_dotenv('.env')

app = Quart(__name__)

app.debug = os.environ.get('QUART_DEBUG')
app.env = os.environ.get('QUART_ENV')
app.secret_key = 'some_key'

app = cors(
    app,
    allow_origin=['http://127.0.0.1:5500'],
    allow_headers=['content-type'],
    allow_credentials=True
)


BASE_EVENTS = [
    'click', 'scroll', 'pageview'
]


@dataclass
class TrackedEvent:
    name: str
    timestamp: str = None
    url: str = None
    css_path: str = field(default_factory=tuple)

    def __pre_init__(self):
        if self.timestamp is None:
            timezone = pytz.UTC
            self.timestamp = datetime.datetime.now(tz=timezone)

    @cached_property
    def fields(self):
        fields = dataclasses.fields(self)
        return list(map(lambda x: x.name, fields))
    
    @cached_property
    def is_custom_event(self):
        return self.name in BASE_EVENTS

    def to_dict(self):
        result = OrderedDict()
        for field in self.fields:
            result[field] = getattr(self, field)
        return result
    
    def to_csv(self):
        result = []
        for field in self.fields:
            result.append(getattr(self, field))
        return result


def write_json(data):
    with open('database.csv', mode='+a', encoding='utf-8', newline='\n') as f:
        writer = csv.writer(f)
        writer.writerow(data)
    # with open('database.json', mode='w+', encoding='utf-8') as f:
    #     previous_data = json.load(f)
    #     print(previous_data)
    #     if previous_data is None:
    #         previous_data = [data]
    #     else:
    #         previous_data.append(data)
    #     json.dump(previous_data, f)


@app.route('/tracking/js', methods=['post'])
async def receive_event():
    data = await request.data
    data = json.loads(data)
    trackable_events = list(map(lambda x: TrackedEvent(**x), data))

    events_queue = Queue()

    async def read_queue():
        while trackable_events:
            event = trackable_events.pop()
            print(event.to_dict())
            # events_queue.put(event.to_dict())
            events_queue.put(event.to_csv())
            await asyncio.sleep(2)

    async def register_event():
        """Registers each event in the
        Redis database"""
        while not events_queue.empty():
            data = events_queue.get()
            write_json(data)
            await asyncio.sleep(4)

    asyncio.gather(read_queue(), register_event())
    return jsonify({'state': True})


if __name__ == '__main__':
    app.run(debug=True)
