import dateparser
from datetime import timedelta
from requests import get
import requests
import json
import datetime
import logging
import voluptuous as vol
from time import sleep
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.components.calendar import GoogleCalendarEventDevice

__version__ = '0.1.3'

_LOGGER = logging.getLogger(__name__)
CONF_NAME = 'name'
CONF_CALENDAR = 'calendar'
CONF_CALENDAR_TYPE = 'type'
DOMAIN = 'google_calender_events'
DEFAULT_NAME = 'Google Calendar Events'
DEFAULT_SCAN_INTERVAL = timedelta(minutes=20)
SCAN_INTERVAL = timedelta(minutes=20)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_CALENDAR, default=DEFAULT_NAME): cv.ensure_list,
})


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    async_add_devices([GoogleCalendarEventsSensor(hass, config)])


class CalendarEvent:
    """ Point class represents and manipulates x,y coords. """

    def __init__(self, _startTime=0, _startDate=0, _endTime=0, _endDate=0, _summary=0, _type='event', _location="", _htmlLink=""):
        """ Create a new point at the origin """
        self._startTime = _startTime
        self._startDate = _startDate
        self._endTime = _endTime
        self._endDate = _endDate
        self._summary = _summary
        self._type = _type
        self._location = _location
        self._htmlLink = _htmlLink

class GoogleCalendarEventsSensor(Entity):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self._name = config[CONF_NAME]
        self._calendarID = config[CONF_CALENDAR]
        # _LOGGER.error(config[CONF_CALENDAR])
        # _LOGGER.error(self._calendarID)
        self._state = None
        self._calendar = []
        self._events = 0
        self.component = loader.get_component(hass, "calendar")
    async def async_added_to_hass(self):
        await self.init()
    async def init(self):
        await self.async_update(self.hass, self.config)
    async def async_update(self, hass, config):
        self._events = 0
        current_date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc,
                                                          hour=0, minute=0, second=0, microsecond=0).isoformat()
        start_date = (datetime.datetime.fromisoformat(
            current_date) + datetime.timedelta(days=1)).isoformat()
        end_date = (datetime.datetime.fromisoformat(start_date) +
                    datetime.timedelta(days=1)).isoformat()
        start_date = start_date[:-6] + "Z"
        end_date = end_date[:-6] + "Z"
        self._calendar = []
        for cal in self._calendarID:         
            _LOGGER.error(cal['id'])
            sleep(20)
            url = f'http://localhost:8123/api/calendars/calendar.{cal["id"]}?start={start_date}&end={end_date}'
            headers = {
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIwZjYyMTg2MjNhZWI0MTEyODI3ZmIyMjE3YzU3ZjU0MyIsImlhdCI6MTU3NTk4NTI0MywiZXhwIjoxODkxMzQ1MjQzfQ.Supw2hjTHoKp6Gj-E7-D5zIf5mzwziKI7ln3digWL0U',
                'content-type': 'application/json',
                'charset': 'utf-8',
                'User-Agent': 'component'
            }
            try:
                response = get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                _LOGGER.error(err)
            _LOGGER.error(response.text)
            data = json.loads(response.text)
            sleep(2)
            for x in data:
                _LOGGER.error("Ddata")
                _LOGGER.error(x)
                calendar_event = CalendarEvent()
                if('recurringEventId' not in x and 'dateTime' in x['start']):
                    calendar_event._startTime = dateparser.parse(
                        x['start']['dateTime']).strftime('%H:%M')
                    calendar_event._startDate = dateparser.parse(
                        x['start']['dateTime']).strftime('%D')
                    calendar_event._endTime = dateparser.parse(
                        x['end']['dateTime']).strftime('%H:%M')
                    calendar_event._endDate = dateparser.parse(
                        x['end']['dateTime']).strftime('%D')
                else:
                    calendar_event._startDate = dateparser.parse(
                        x['start']['date']).strftime('%D')
                if('type' in cal):
                    calendar_event._type = cal['type']
                else:
                    calendar_event._summary = x['summary']
                if('summary' in x):
                    _LOGGER.error("Simm")
                    _LOGGER.error(x)
                    _LOGGER.error(x['summary'])
                    #summ_split = x['summary'].split(":")[1]
                    #summ_split = summ_split.split(".")[0]
                    summ_split = x['summary']
                    calendar_event._summary = summ_split
                else:
                    _LOGGER.error("No summary")
                if('location' in x):
                    calendar_event._location = x['location']
                calendar_event._htmlLink = x['htmlLink']
                self._calendar.append(calendar_event.__dict__)
                self._events = self._events + 1

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return 'mdi:calendar-blank-multiple'

    @property
    def device_state_attributes(self):
        return {
            'calendar': self._calendar,
            'name': self._name,
            'events': self._events
        }


    
